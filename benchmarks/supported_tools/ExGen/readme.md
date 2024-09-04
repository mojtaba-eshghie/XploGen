# Cross-platform Automatic Exploit Generation for Smart Contracts

This tool contains four main modules.

### pre-requisites

```
> brew install llvm@7
> echo 'export PATH="/usr/local/opt/llvm@7/bin:$PATH"' >> ~/.zshrc
> source ~/.zshrc
> pip3 install llvmlite==0.31.0 solidity_parser==0.0.7
```

### 1. sol2ll-frontend-python

A Solidity frontend based on [python-solidity-parser](https://github.com/ConsenSys/python-solidity-parser), which translates Solidity into LLVM for Ethereum Smart Contracts.

Usage: 
```
> cd anonymous/sol2ll-frontend-python
> python3 sol2ll-frontend-python.py <dataset path> <log file path>
```

Example:
```
> cd anonymous/sol2ll-frontend-python
> python3 sol2ll-frontend-python.py ./test/ ./test/frontend.log
```

There is a sample Solidity file called "simple.sol" and the frontend will output a corresponding LLVM file "simple.ll" in same directory.

### 2. backward-analyzer

A backward analyzer performing taint analysis and backward control/dataflow tracking, which outputs Partially-ordered Transactional Set (PTS) in JSON format.

Usage:

```
> cd anonymous/backward-analyzer
> python3 backward-analyzer.py <dataset path> <log file path> <vulnerability type: 1. intflow 2. reentrancy 3. teether>
```

Example:

```
> cd anonymous/backward-analyzer
> python3 backward-analyzer.py ../sol2ll-frontend-python/test/ ../sol2ll-frontend-python/test/backward.log intflow
```

There is a sample LLVM file "simple.ll" (translated from "simple.sol") and the analyzer will output PTSes to a corresponding JSON file "simple.json" in same directory.

### 3. KleeTool

This tool initializes state variables with values crawled from blockchain.

### 4. KLEE

A modified symbolic executor based on [KLEE v2.1](https://klee.github.io/releases/docs/v2.1/), which symbolically executes smart contracts in LLVM IR to solve the constraints.

