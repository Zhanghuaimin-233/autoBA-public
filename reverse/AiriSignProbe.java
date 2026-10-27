import com.github.unidbg.AndroidEmulator;
import com.github.unidbg.Emulator;
import com.github.unidbg.LibraryResolver;
import com.github.unidbg.Module;
import com.github.unidbg.arm.context.RegisterContext;
import com.github.unidbg.debugger.BreakPointCallback;
import com.github.unidbg.linux.android.AndroidEmulatorBuilder;
import com.github.unidbg.linux.android.AndroidResolver;
import com.github.unidbg.linux.android.dvm.AbstractJni;
import com.github.unidbg.linux.android.dvm.DalvikModule;
import com.github.unidbg.linux.android.dvm.DvmClass;
import com.github.unidbg.linux.android.dvm.DvmObject;
import com.github.unidbg.linux.android.dvm.VM;
import com.github.unidbg.linux.android.dvm.array.ByteArray;
import com.github.unidbg.memory.Memory;
import com.github.unidbg.pointer.UnidbgPointer;

import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Paths;

/**
 * 逆向用 harness（复制自 unidbg-work/AiriSignRunner.java，原文件未改动）。
 * 用法:
 *   java -cp "jars/*;<reverse 目录>" AiriSignProbe <so> <input> <mode> [traceLenHex] [traceFile]
 * input: utf8:<text> | hex:<hexbytes> | file:<path>
 * 例: AiriSignProbe libairisgcore.so utf8:test 0
 *     AiriSignProbe libairisgcore.so hex:00ff10 1 8000 reverse/trace_m1.txt
 */
public class AiriSignProbe extends AbstractJni {

    private final AndroidEmulator emulator;
    private final VM vm;
    private Module module;

    public AiriSignProbe() {
        emulator = AndroidEmulatorBuilder.for64Bit()
                .setProcessName("com.RoamingStar.BlueArchive")
                .build();
        Memory memory = emulator.getMemory();
        LibraryResolver resolver = new AndroidResolver(23);
        memory.setLibraryResolver(resolver);
        vm = emulator.createDalvikVM();
        vm.setJni(this);
        vm.setVerbose(false);
    }

    public void load(String soPath) {
        File so = new File(soPath);
        DalvikModule dm = vm.loadLibrary(so, false);
        module = dm.getModule();
        try {
            dm.callJNI_OnLoad(emulator);
        } catch (Throwable t) {
            System.out.println("[!] JNI_OnLoad 异常(继续): " + t.getMessage());
        }
    }

    public UnidbgPointer nativeSign() {
        DvmClass clazz = vm.resolveClass("com/airi/core/sign/AiriSgClient");
        return clazz.findNativeFunction(emulator, "sign([BI)Ljava/lang/String;");
    }

    public String sign(byte[] data, int mode) {
        DvmClass clazz = vm.resolveClass("com/airi/core/sign/AiriSgClient");
        ByteArray arr = new ByteArray(vm, data);
        DvmObject<?> ret = clazz.callStaticJniMethodObject(
                emulator, "sign([BI)Ljava/lang/String;", arr, mode);
        return ret == null ? null : (String) ret.getValue();
    }

    private static byte[] decode(String spec) throws Exception {
        if (spec.startsWith("utf8:")) {
            return spec.substring(5).getBytes("UTF-8");
        } else if (spec.startsWith("hex:")) {
            String h = spec.substring(4).replace(" ", "");
            byte[] out = new byte[h.length() / 2];
            for (int i = 0; i < out.length; i++) {
                out[i] = (byte) Integer.parseInt(h.substring(i * 2, i * 2 + 2), 16);
            }
            return out;
        } else if (spec.startsWith("file:")) {
            return Files.readAllBytes(Paths.get(spec.substring(5)));
        }
        throw new IllegalArgumentException("bad input spec: " + spec);
    }

    private static String hex(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (byte x : b) sb.append(String.format("%02x", x & 0xff));
        return sb.toString();
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.out.println("usage: AiriSignProbe <so> <utf8:|hex:|file:> <mode> [traceLenHex] [traceFile]");
            return;
        }
        String soPath = args[0];
        String spec = args[1];
        int mode = Integer.parseInt(args[2]);
        byte[] data = decode(spec);

        AiriSignProbe runner = new AiriSignProbe();
        runner.load(soPath);

        UnidbgPointer fn = runner.nativeSign();
        long base = runner.module.base;
        long addr = fn.peer;
        System.out.printf("[module] base=0x%x size=0x%x path=%s%n",
                base, runner.module.size, runner.module.getPath());
        System.out.printf("[native] sign addr=0x%x offset=0x%x%n", addr, addr - base);
        System.out.printf("[input] len=%d hex=%s%n", data.length, hex(data));

        PrintStream traceOut = null;
        if (args.length >= 5) {
            long len = Long.parseLong(args[3], 16);
            traceOut = new PrintStream(new FileOutputStream(args[4]), true);
            runner.emulator.traceCode(addr, addr + len).setRedirect(traceOut);
            System.out.printf("[trace] range=0x%x..0x%x -> %s%n", addr, addr + len, args[4]);
        }

        runner.emulator.attach().addBreakPoint(addr, new BreakPointCallback() {
            @Override
            public boolean onHit(Emulator<?> emu, long address) {
                RegisterContext ctx = emu.getContext();
                System.out.printf("[entry] pc=0x%x x0=0x%x x1=0x%x x2=0x%x x3=0x%x lr=0x%x sp=0x%x%n",
                        ctx.getPCPointer().peer,
                        ctx.getLongArg(0), ctx.getLongArg(1), ctx.getLongArg(2), ctx.getLongArg(3),
                        ctx.getLR(), ctx.getStackPointer().peer);
                return true;
            }
        });

        String sig = runner.sign(data, mode);
        System.out.println("[signature] " + sig);
        if (sig != null) {
            byte[] raw = java.util.Base64.getDecoder().decode(sig);
            System.out.printf("[sigbytes] len=%d hex=%s%n", raw.length, hex(raw));
        }
        if (traceOut != null) {
            traceOut.flush();
            traceOut.close();
        }
        runner.emulator.close();
    }
}
