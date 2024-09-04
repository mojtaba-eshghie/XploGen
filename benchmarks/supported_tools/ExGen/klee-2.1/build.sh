if [ -d "./build" ];then
rm -rf ./build
fi

mkdir build
cd build

cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_SOLVER_STP=OFF \
  -ENABLE_SOLVER_Z3=ON \
  -DENABLE_POSIX_RUNTIME=ON \
  -DENABLE_KLEE_UCLIBC=ON \
  -DENABLE_UNIT_TESTS=OFF \
  -DKLEE_UCLIBC_PATH=/home/zode/Software/klee-2.1/klee-uclibc \
  -DLLVM_CONFIG_BINARY=/opt/llvm70/bin/llvm-config \
  -DLLVMCC=/opt/llvm70/bin/clang \
  -DLLVMCXX=/opt/llvm70/bin/clang++ \
  ..

make -j6
sudo make install
