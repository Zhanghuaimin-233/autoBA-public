import com.github.unidbg.AndroidEmulator;
import com.github.unidbg.LibraryResolver;
import com.github.unidbg.linux.android.AndroidEmulatorBuilder;
import com.github.unidbg.linux.android.AndroidResolver;
import com.github.unidbg.linux.android.dvm.*;
import com.github.unidbg.memory.Memory;
import com.github.unidbg.Module;
import com.github.unidbg.linux.android.dvm.array.ByteArray;

import java.io.File;

/**
 * AiriSgClient sign 函数的 unidbg 离线调用器。
 *
 * 用法: java -cp "jars/*;." AiriSignRunner <so路径> "<待签名文本>" [mode]
 * 验证基准(oracle 实测): sign("test", 0) 输出与游戏内调用逐字节一致
 *
 * 说明：本类仅用于协议学习与研究。签名结果确定性（同输入同输出）。
 */
public class AiriSignRunner extends AbstractJni {

    private final AndroidEmulator emulator;
    private final VM vm;
    private Module module;

    public AiriSignRunner() {
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
            System.out.println("[+] JNI_OnLoad 完成");
        } catch (Throwable t) {
            System.out.println("[!] JNI_OnLoad 异常(继续): " + t.getMessage());
        }
    }

    public String sign(String text, int mode) {
        DvmClass clazz = vm.resolveClass("com/airi/core/sign/AiriSgClient");
        byte[] data = text.getBytes();
        ByteArray arr = new ByteArray(vm, data);
        DvmObject<?> ret = clazz.callStaticJniMethodObject(
                emulator, "sign([BI)Ljava/lang/String;", arr, mode);
        return ret == null ? null : (String) ret.getValue();
    }

    public static void main(String[] args) throws Exception {
        String soPath = args.length > 0 ? args[0] : "capture/libairisgcore.so";
        String text = args.length > 1 ? args[1] : "test";
        int mode = args.length > 2 ? Integer.parseInt(args[2]) : 0;

        AiriSignRunner runner = new AiriSignRunner();
        runner.load(soPath);

        try {
            String sig = runner.sign(text, mode);
            System.out.println("[sign(\"" + text + "\", " + mode + ")] " + sig);
        } catch (Throwable t) {
            System.out.println("[!] sign 调用失败: " + t);
            t.printStackTrace();
        }
        runner.emulator.close();
    }
}
