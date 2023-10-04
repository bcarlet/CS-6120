#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

using namespace llvm;

namespace {

struct TDCE: public PassInfoMixin<TDCE> {
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM);
};

PreservedAnalyses TDCE::run(Module &M, ModuleAnalysisManager &AM) {
    for (auto &F : M) {
        for (auto &B : F) {
            auto I = B.begin();

            while (I != B.end()) {
                if (I->use_empty() && I->isSafeToRemove()) {
                    I = I->eraseFromParent();

                    errs() << "Unused: " << *I << '\n';
                }
                else {
                    ++I;
                }
            }
        }
    }

    return PreservedAnalyses::none();
};

}

extern "C" LLVM_ATTRIBUTE_WEAK
PassPluginLibraryInfo llvmGetPassPluginInfo() {
    auto registerCallbacks =
        [](PassBuilder &PB) {
            PB.registerPipelineStartEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel) {
                    MPM.addPass(TDCE());
                }
            );
        };

    return {
        LLVM_PLUGIN_API_VERSION,
        "Trivial dead code elimination",
        "v0.1",
        registerCallbacks
    };
}
