//
// Created by xxxx on xxxx/xx/xx.
//
#ifndef KLEE_MODIFYLLVM_H
#define KLEE_MODIFYLLVM_H

#include "Controller.h"

#include <cstring>
#include <set>
#include <string>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

/**
 * @brief Only the arithmetic instruction needs klee_assume()
 */
class KleeAssume {
  //    %11 = load i32, i32* %3
  //    %12 = icmp sgt i32 %11, 0
  //    %13 = zext i1 %12 to i32
  //    %14 = sext i32 %13 to i64
  //    call void @klee_assume(i64 %14)
 public:
  KleeAssume() : count(0) {}

  // 1:Add 2:sub
  KleeAssume(int _opType,
             int _num,
             RegName* _nameL,
             RegName* _nameR,
             string _inst,
             bool _first) {
    inst = std::move(_inst);
    count = 1;
    string tmpStr;
    string tmpRes;
    string tmpOp;

    tmpRes =
        "%\"tmpAssume_" + to_string(_num) + ("." + to_string(count)) + "\"";
    if (_first) {
      if (_opType == 1)
        tmpOp = "icmp ult " + _nameL->GetString() + ", " + _nameR->GetName();
      else if (_opType == 2)
        tmpOp = "icmp ugt " + _nameL->GetString() + ", " + _nameR->GetName();
    } else {
      if (_opType == 1) tmpOp = "icmp ult " + _nameL->GetString() + ", 0";
      else if (_opType == 2)
        tmpOp = "icmp ugt " + _nameL->GetString() + ", 0";
    }
    tmpStr = tmpRes;
    newStr.push_back("  " + tmpRes + " = " + tmpOp);
    count++;

    tmpRes =
        "%\"tmpAssume_" + to_string(_num) + ("." + to_string(count)) + "\"";
    tmpOp = "zext i1 " + tmpStr + " to i32";
    tmpStr = tmpRes;
    newStr.push_back("  " + tmpRes + " = " + tmpOp);
    count++;

    tmpRes =
        "%\"tmpAssume_" + to_string(_num) + ("." + to_string(count)) + "\"";
    tmpOp = "sext i32 " + tmpStr + " to i64";
    tmpStr = tmpRes;
    newStr.push_back("  " + tmpRes + " = " + tmpOp);

    newStr.push_back("  call void @klee_assume(i64 " + tmpStr + ")");
  }

  void Show() {
    for (const string& line : newStr) cout << line << endl;
  }

  vector<string> GetNewStr() {
    return newStr;
  }

  string GetInst() {
    return inst;
  }

 private:
  string inst;
  int count;
  vector<string> newStr;
};

class SymDecl {
 public:
  SymDecl() = default;

  void Init() {}

 private:
  pair<int, RegName> syms;
};

class LLVMFunction {
 public:
  LLVMFunction() : startLine(0), endLine(0) {}

  LLVMFunction(int _startLine,
               int _endLine,
               string _funcName,
               const vector<string>& _funcLines) {
    //        symCount = 0;
    startLine = _startLine;
    endLine = _endLine;
    funcName = std::move(_funcName);
    funcLines = _funcLines;
    newLines = _funcLines;
  }

  vector<string> GetLines() {
    return funcLines;
  }

  vector<string> GetNewLines() {
    return newLines;
  }

  void Refresh() {
    newLines = vector<string>(funcLines);
  }

  void WriteNewLines(vector<string> _newLines) {
    newLines = std::move(_newLines);
  }

  void AddAssume(int _opType,
                 int _num,
                 RegName* _nameL,
                 RegName* _nameR,
                 const string& _inst,
                 bool _first) {
    kleeAssumes.emplace_back(_opType, _num, _nameL, _nameR, _inst, _first);
  }

  vector<KleeAssume> GetAssumes() {
    return kleeAssumes;
  }

  void ClearAssume() {
    kleeAssumes.clear();
  }

  vector<string> GetAssumeStr() {
    vector<string> _res;
    for (auto kleeAssume : kleeAssumes) {
      vector<string> tmp = kleeAssume.GetNewStr();
      _res.insert(_res.end(), tmp.begin(), tmp.end());
    }
    return _res;
  }

  string GetName() {
    return funcName;
  }

  int StartLine() {
    return startLine;
  }

  int EndLine() {
    return endLine;
  }

  void ShowAssume() {
    for (auto kleeAssume : kleeAssumes) { kleeAssume.Show(); }
  }

  void Show() {
    for (const auto& funcLine : funcLines) cout << funcLine << endl;
  }

  /*  void AddGlobalSymDecl(RegName* _reg) {
      string _res = "@.str";
      _res += symCount == 0 ? "" : "." + to_string(symCount);
      _res += " = private unnamed_addr constant [";
      _res += to_string(_reg->GetPureName().size() + 1);
      _res += " x i8] c\"" + _reg->GetPureName() + "\\00\"";

      cout << "debug: " << _res << endl;
      globalSymDecls.push_back(_res);
      // str = private unnamed_addr constant [2 x i8] c"x\00";
    }*/

 public:
  //    int symCount;

 private:
  //    vector<string> globalSymDecls;
  vector<SymDecl> symDecls;
  vector<KleeAssume> kleeAssumes;

  int startLine;
  int endLine;
  string funcName;
  vector<string> newLines;
  vector<string> funcLines;
};

class LLVMFuncChain {
 public:
  LLVMFuncChain() = default;

  void Init(int _size) {
    LLVMFunctions.resize(_size);
  }

  /*  LLVMFunction& GetLLVMFunction(const string& _name) {
      LLVMFunction res;
      for (LLVMFunction& func : LLVMFunctions) {
        if (func.GetName() == _name) {
          return func;
        }
      }
      return res;
    }*/

 private:
  // 一个函数调用链
  vector<LLVMFunction> LLVMFunctions;
};

class LLVMFile {
 public:
  LLVMFile() : symCount(0) {
    kleeSymDecl = "declare void @klee_make_symbolic(i8*, i64, i8*)";
    kleeAssumeDecl = "declare void @klee_assume(i64)";
  };

  explicit LLVMFile(const string& _name, const string& _path, int _size) {
    kleeSymDecl = "declare void @klee_make_symbolic(i8*, i64, i8*)";
    kleeAssumeDecl = "declare void @klee_assume(i64)";

    symCount = 0;
    fileName = _name;
    filePath = _path;
    llFile.open(_path + "/" + fileName, ios::in);
    // cout << "debug " << _path + "/" + fileName << endl;
    if (!llFile.is_open()) cout << "Invalid llvm file!" << endl;

    string tmpLine;
    while (getline(llFile, tmpLine)) {
      fileLines.emplace_back(tmpLine);
      //  cout << "!!!" << tmpLine << endl;
    }
    originFileLines.assign(fileLines.begin(), fileLines.end());
    llFile.close();

    funcChains.resize(_size);
  }

  LLVMFuncChain GetLLVMChain(int _index) {
    return funcChains[_index];
  }

  string GetFileName() {
    return fileName;
  }

  // Substitution function
  void Replace(int _start, int _end, vector<string> _newStr) {
    vector<string>::iterator iter;
    iter = fileLines.erase(fileLines.begin() + _start,
                           fileLines.begin() + _end + 1);
    fileLines.insert(iter, _newStr.begin(), _newStr.end());
  }

  /**
   * Returns the number of lines and functions in the file
   * @param _funcName
   * @return
   */
  LLVMFunction InitFuncLines(const string& _funcName) {
    int startLine = 0, endLine = 0;
    vector<string> funcLines;

    bool inThisFunc = false;
    regex funcRex;
    smatch funcRexRes;
    string tmpStr("define .* @" + _funcName + R"(\(.*\))");
    for (int i = 0; i < tmpStr.length(); i++) {
      if (tmpStr[i] == '$') {
        tmpStr[i] = '\\';
        tmpStr.insert(tmpStr.begin() + i + 1, '$');
        i++;
      }
    }
    //    cout << tmpStr << endl;
    funcRex = tmpStr;

    //        cout << "!!!" << _funcName << endl;

    for (int i = 0; i < fileLines.size(); ++i) {
      string fileLine = fileLines[i];
      //            cout << "!!!" << fileLine << endl;
      if (inThisFunc) {
        funcLines.push_back(fileLine);
        if (fileLine.find('}') != string::npos) {
          endLine = i;
          inThisFunc = false;
          break;
        }
      } else {
        if (regex_search(fileLine, funcRexRes, funcRex)) {
          startLine = i;
          //  cout << "!!!" << endl;
          funcLines.push_back(fileLine);
          inThisFunc = true;
        }
      }
    }

    LLVMFunction _res(startLine, endLine, _funcName, funcLines);
    llvmFunctions.emplace(_funcName, _res);

    return _res;
  }

  unordered_map<string, LLVMFunction> GetLLFuncs() {
    return llvmFunctions;
  }

  void ReturnLLFunc(const string& _funcName, LLVMFunction& _llFunc) {
    llvmFunctions[_funcName] = _llFunc;
  }

  vector<string> GetFileLines() {
    return fileLines;
  }

  // Create a new file
  void CreateFile(const string& _newName) {
    ofstream newFile(filePath + "/" + _newName, ios::out);
    for (const auto& fileLine : fileLines) newFile << fileLine << endl;

    newFile << kleeSymDecl << endl;
    newFile << kleeAssumeDecl << endl;
  }

  int AddGlobalSymDecl(RegName* _reg) {
    if (globalSyms.find(_reg->GetPureName()) == localSyms.end()) {
      string _res = "@klee_str";
      _res += symCount == 0 ? "" : "." + to_string(symCount);
      _res += " = private unnamed_addr constant [";
      _res += to_string(_reg->GetPureName().size() + 1);
      _res += " x i8] c\"" + _reg->GetPureName() + "\\00\"";
      // cout << "debug: " << _res << endl;
      globalSymDecls.emplace_back(_res, _reg);
      globalSyms.emplace(_reg->GetPureName(), Symbol(symCount, _res));
      symCount++;
    }

    return globalSyms[_reg->GetPureName()].GetNum();
  }

  int AddLocalSymDecl(RegName* _reg) {
    if (localSyms.find(_reg->GetPureName()) == localSyms.end()) {
      string _res = "@klee_str";
      _res += symCount == 0 ? "" : "." + to_string(symCount);
      _res += " = private unnamed_addr constant [";
      _res += to_string(_reg->GetPureName().size() + 1);
      _res += " x i8] c\"" + _reg->GetPureName() + "\\00\"";
      // cout << "debug: " << _res << endl;
      localSymDecls.emplace_back(_res, _reg);
      localSyms.emplace(_reg->GetPureName(), Symbol(symCount, _res));
      symCount++;
    }

    return localSyms[_reg->GetPureName()].GetNum();
  }

  void RemoveLoacalSymDecl(RegName* _reg) {
    localSyms.erase(_reg->GetPureName());
    symCount--;
  }

  inline int FindSize(const string& _type) {
    int resSize = 0;
    regex typeDef(R"( = type \{ (.*) \})");
    smatch typeDefRes;
    for (auto& fileLine : fileLines) {
      if (fileLine.find("define ") != string::npos) break;
      if (fileLine.find(_type + " = type") != string::npos) {
        if (regex_search(fileLine, typeDefRes, typeDef)) {
          vector<string> argTypes;
          string _types(typeDefRes[1].str());
          regex structRex(R"((%[\"]*[\w\.\:]*[\"]*))");
          regex typeIntDef(R"(i\d+)");
          regex typePtrDef(R"([%\"\w\.\:]*\*)");
          regex typeArray(R"(\[(\d+) x i(\d+)\])");
          smatch structRexRes, intRexRes, ptrRexRes, arrayRexRes;
          string tmp;
          while (!_types.empty()) {
            tmp = _types;
            if (regex_search(_types, ptrRexRes, typePtrDef))
              argTypes.push_back(ptrRexRes[0].str());
            else if (regex_search(_types, structRexRes, structRex))
              argTypes.push_back(structRexRes[1].str());
            else if (regex_search(_types, intRexRes, typeIntDef))
              argTypes.push_back(intRexRes[0].str());
            else if (regex_search(_types, arrayRexRes, typeArray))
              argTypes.push_back(arrayRexRes[0].str());

            int pos = _types.find(argTypes.back());
            if (pos != string::npos)
              _types.erase(pos, argTypes.back().length());
            if (_types[0] == ',') _types.erase(0, 2);
            if (_types[0] == ' ') _types.erase(0, 1);
            if (tmp == _types) return 0;
          }
          // Read each member
          regex typeIntSize(R"(i(\d+))");
          smatch intSizeRes, typePtrDefRes;
          for (const auto& argType : argTypes) {
            if (regex_match(argType, intSizeRes, typeIntSize))
              resSize += stoi(intSizeRes[1].str()) / 8;
            else if (regex_match(argType, typePtrDefRes, typePtrDef))
              resSize += 4;
            else if (regex_search(_types, arrayRexRes, typeArray))
              resSize += stoi(arrayRexRes[1].str()) * stoi(arrayRexRes[2]) / 8;
            else
              resSize += FindSize(argType);
          }
          break;
        }
      }
    }
    return resSize;
  }

  int AddLocalSymDecl(LLVMFunction _llvmFunc) {
    FuncDefine func;
    smatch funcRes;
    vector<string> funcLines = _llvmFunc.GetNewLines();
    string defineStr = funcLines.front();
    // cout << "debug: " << defineStr << endl;
    regex funcRex(
        R"(define[ linkonce_odr]*[ weak]*[ interal]*[ hidden]*[ dso_local]* (.*) [@%\"]*([\w+\$]*)[\"]*\((.*)\))");
    if (regex_search(defineStr, funcRes, funcRex)) func.Init(funcRes);
    int lineCount = 0;
    for (auto arg : func.GetArgs()) {
      string argType = arg.GetType();
      string argName = arg.GetName();
      // If the first parameter for EOS, the contract itself, skipped
      if (argType.find("%") != string::npos &&
          argName.find("0") != string::npos)
        continue;
      // Temporary store instruction
      string tmpStoreStr("store " + arg.GetString() + ", ");
      // A temporary register object
      RegName* _source =
          new RegName(arg.GetType(), arg.GetAttr(), arg.GetThisName(),
                      arg.GetCount(), arg.GetHasQuote());
      // A temporary string used for substitution
      vector<string> tmpLines;
      string tmpLine;
      // If the type itself is a pointer
      if (argType.find("*") != string::npos) {
        // Current global symbol value
        int num = AddLocalSymDecl(_source);
        tmpLines.push_back("  %\"bitcast_" + to_string(num) + "\" = bitcast " +
                           _source->GetString() + " to i8*");
        tmpLine = "  call void @klee_make_symbolic(i8* " +
                  ("%\"bitcast_" + to_string(num) + "\"");

        int sourceSize = 0;
        if (_source->GetSize() == 0) {
          // Find the size from the global declaration
          string _type = _source->GetType();
          int pos = _type.find('*');
          if (pos != string::npos) _type.erase(pos, 1);
          sourceSize = FindSize(_type);
        } else
          sourceSize = _source->GetSize() / 8;
        if (sourceSize != 0) {
          tmpLine += ", i64 " + to_string(sourceSize);
          tmpLine += ", i8* getelementptr inbounds ([";
          tmpLine += to_string(_source->GetPureName().size() + 1) +
                     " x i8], [" +
                     to_string(_source->GetPureName().size() + 1) +
                     " x i8]* @klee_str";
          tmpLine += num == 0 ? "" : "." + to_string(num);
          tmpLine += ", i64 0, i64 0))";
          tmpLines.push_back(tmpLine);
        } else {
          RemoveLoacalSymDecl(_source);
          tmpLines.clear();
        }
      } else {  // If it's not a pointer you have to write your own store
        RegName* _dest = new RegName(_source->GetType() + "*", "%",
                                     "myDest_" + to_string(symCount), 0, false);
        // 当前全局符号数值
        int num = AddLocalSymDecl(_source);
        string myAllocInst("  " + _dest->GetName() + " = alloca " +
                           _source->GetType());
        tmpLines.push_back(myAllocInst);
        string myStoreInst("  store " + _source->GetString() + ", " +
                           _dest->GetString());
        tmpLines.push_back(myStoreInst);
        tmpLines.push_back("  %\"bitcast_" + to_string(num) + "\" = bitcast " +
                           _dest->GetString() + " to i8*");
        tmpLine = "  call void @klee_make_symbolic(i8* " +
                  ("%\"bitcast_" + to_string(num) + "\"");
        // TODO might also need to determine size here
        tmpLine += ", i64 " + to_string(_dest->GetSize() / 8);
        tmpLine += ", i8* getelementptr inbounds ([";
        tmpLine += to_string(_source->GetPureName().size() + 1) + " x i8], [" +
                   to_string(_source->GetPureName().size() + 1) +
                   " x i8]* @klee_str";
        tmpLine += num == 0 ? "" : "." + to_string(num);
        tmpLine += ", i64 0, i64 0))";
        tmpLines.push_back(tmpLine);
      }
      if (!tmpLines.empty())
        funcLines.insert(funcLines.begin() + 1 + lineCount, tmpLines.begin(),
                         tmpLines.end());
      lineCount += tmpLines.size();
    }
    int argsCount = func.GetArgs().size();
    vector<string> testFunc;
    testFunc.emplace_back("define internal void @klee_test() #0 {");
    // Add the test call
    for (int i = 0; i < 2 * argsCount; i++) {
      if (i < argsCount) {
        if (func.GetArgs()[i].GetType().empty())
          testFunc.push_back("  %" + to_string(i + 1) + " = alloca " +
                             func.GetFunc()->GetType());
        else
          testFunc.push_back("  %" + to_string(i + 1) + " = alloca " +
                             func.GetArgs()[i].GetType());
      } else {
        if (func.GetArgs()[i - argsCount].GetType().empty())
          testFunc.push_back("  %" + to_string(i + 1) + " = load " +
                             func.GetFunc()->GetType() + ", " +
                             func.GetFunc()->GetType() + "* %" +
                             to_string(i + 1 - argsCount));
        else
          testFunc.push_back("  %" + to_string(i + 1) + " = load " +
                             func.GetArgs()[i - argsCount].GetType() + ", " +
                             func.GetArgs()[i - argsCount].GetType() + "* %" +
                             to_string(i + 1 - argsCount));
      }
    }
    //    string defineLine = funcLines.front();
    if (func.GetFunc()->GetType().find("void") == string::npos) {
      testFunc.push_back("  %" + to_string(2 * argsCount + 1) + " = call " +
                         func.GetFunc()->GetString());
      testFunc.back() += "(";
      if (!func.GetArgs().empty() && !func.GetArgs()[0].GetType().empty())
        testFunc.back() +=
            func.GetArgs()[0].GetType() + " %" + to_string(argsCount + 1);
      for (int i = 1; i < argsCount; i++) {
        if (func.GetArgs()[0].GetType().empty()) continue;
        testFunc.back() += ", " + func.GetArgs()[i].GetType() + " %" +
                           to_string(i + argsCount + 1);
      }
    } else {
      testFunc.push_back("  call " + func.GetFunc()->GetString());
      testFunc.back() +=
          "(" + func.GetArgs()[0].GetType() + " %" + to_string(argsCount + 1);
      for (int i = 1; i < argsCount; i++) {
        testFunc.back() += ", " + func.GetArgs()[i].GetType() + " %" +
                           to_string(i + argsCount + 1);
      }
    }
    testFunc.back() += ")";
    testFunc.emplace_back("  ret void");
    testFunc.emplace_back("}");

    funcLines.emplace_back("");
    funcLines.insert(funcLines.end(), testFunc.begin(), testFunc.end());

    _llvmFunc.WriteNewLines(funcLines);
    Replace(_llvmFunc.StartLine(), _llvmFunc.EndLine(), funcLines);
    return func.GetArgs().size();
  }

  void WriteGlobalSymDecl() {
    int lineNum = 2;
    for (auto _tmp : globalSymDecls) {
      for (int i = 0; i < fileLines.size(); ++i) {
        if (fileLines[i].find(_tmp.second->GetName() + " = ") != string::npos) {
          fileLines.insert(fileLines.begin() + i + 1, _tmp.first);
          lineNum = i + 1;
          break;
        }
      }
    }
    if (lineNum == 2) {
      while (!fileLines[lineNum].empty()) lineNum++;
    }
    for (const auto& _tmp : localSymDecls) {
      fileLines.insert(fileLines.begin() + (++lineNum), _tmp.first);
    }
  }

  void AddGlobalSymbols(RegName* _reg) {
    globalSymbols.emplace(_reg);
    symCount++;
  }

  void Refresh() {
    fileLines.assign(originFileLines.begin(), originFileLines.end());
    symCount = 0;
    globalSymDecls.clear();
    localSymDecls.clear();
    globalSyms.clear();
    localSyms.clear();
  }

  void SetTmpLines() {
    tmpFileLines = vector<string>(fileLines);
  }

  void RefreshLines() {
    fileLines = vector<string>(tmpFileLines);
    globalSymbols.clear();
  }

 public:
  int symCount;

 private:
  fstream llFile;

 private:
  unordered_map<string, LLVMFunction> llvmFunctions;
  // Global variables for store and Load
  set<RegName*> globalSymbols;

  unordered_map<string, Symbol> globalSyms;
  unordered_map<string, Symbol> localSyms;

  vector<pair<string, RegName*>> globalSymDecls;
  vector<pair<string, RegName*>> localSymDecls;

  string fileName;
  string filePath;

  vector<string> tmpFileLines;
  vector<string> fileLines;
  vector<string> originFileLines;
  //    string fileLine;

  vector<LLVMFuncChain> funcChains;

  string kleeSymDecl;
  string kleeAssumeDecl;
};

class ModifyLLVM {
 public:
  ModifyLLVM(const string& _name, const string& _path, int _count) {
    llvmFile = new LLVMFile(_name, _path, _count);
  }

  //    void Modify(const string &_instStr, LLVMFunction _llFunction);

  vector<string>
  ModifyArithInst(ArithOp* _inst, int _num, LLVMFunction& _llFunction);

  vector<string> ModifyCallInst(FuncCall* _inst, LLVMFunction& _llFunction);

  vector<string> ModifyStoreInst(StoreInst* _inst, LLVMFunction& _llFunction);

  vector<string> ModifyAssumes(LLVMFunction& _llFunction,
                               vector<KleeAssume> _assumes,
                               const vector<string>& _newStr);

  vector<string> AddArithGlobalSyms(LLVMFunction& _llFunction,
                                    const string& _inst);

  LLVMFile* GetLLVMFile() {
    return llvmFile;
  }

 private:
  LLVMFile* llvmFile;
  //    vector<KleeAssume> kleeAssume;

 private:
  string globalSymDecl;
};

void configArgv(const string& tmpArgv);

#endif  // KLEE_MODIFYLLVM_H
