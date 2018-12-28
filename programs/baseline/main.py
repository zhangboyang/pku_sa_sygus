
# -*- coding: utf-8 -*-

import sys
import sexp
import pprint
import translator
import operator
import fcntl

import re

def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)


ArrayArgs = []
OtherArgs = []
ArrayMode = False

Productions = None
Type = None

FuncDefineStr = None
FuncInvokeStr = None

def CountStmts(Stmts):
    ret = [0, 0]  # (非终结符数, 终结符数)
    
    if not type(Stmts) == list:
        Stmts = [Stmts]

    for i in range(len(Stmts)):
        if type(Stmts[i]) == list:
            next = CountStmts(Stmts[i])
            ret[0] = ret[0] + next[0]
            ret[1] = ret[1] + next[1]
        elif Productions.has_key(Stmts[i]):
            ret[0] = ret[0] + 1
        else:
            ret[1] = ret[1] + 1
    #print "Count:", Stmts, "=", ret
    return ret

def HasSpecialStmt(Stmts):
    if not type(Stmts) == list:
        Stmts = [Stmts]
    for i in range(len(Stmts)):
        if type(Stmts[i]) == list:
            if HasSpecialStmt(Stmts[i]):
                return True
        elif Stmts[i].startswith("$"):
            return True
    return False

def IsBoundLegal(Stmts):
    if HasSpecialStmt(Stmts):
        return False
    boundc = CountStmts(Stmts)
    return boundc[0] + boundc[1] <= 3

def IsBodyLegal(Stmts):
    bodyc = CountStmts(Stmts)
    return bodyc[0] <= 3

def IsLegal(Stmts):
    #print "IsLegal:", CountStmts(Stmts[0]),  CountStmts(Stmts[1]), Stmts
    if not IsBoundLegal(Stmts[0]):
        return False
    #if not IsBodyLegal(Stmts[1]):
    #    return False
    return True


def MakeInvokeStr(prefix):
    return "(" + prefix + FuncInvokeStr[1:]
def MakeDefineStr(prefix, stmt):
    return "(define-fun " + prefix + FuncDefineStr[12:-1] + ' ' + stmt + FuncDefineStr[-1]  # insert Program just before the last bracket ')'

def CompileToMultipleFunc(Stmts):
    BoundStr = MakeDefineStr("LBOUND_", translator.toString(Stmts[0]))
    ret = [BoundStr]

    for i in xrange(len(ArrayArgs)-1, -1, -1):
        nextName = "L%d_" % (i + 1) if i < len(ArrayArgs) - 1 else "LBOUND_"
        currName = "L%d_" % i if i > 0 else ""
        IStr = MakeInvokeStr(nextName)
        #print(IStr)
        Str = MakeDefineStr(currName, translator.toString(Stmts[1])) \
            .replace("$NEXT", IStr) \
            .replace("$AELE", ArrayArgs[i]) \
            .replace("$AIDX", str(i)) \
            #.replace("$ANID", str(i + 1)) \
            #.replace("$APID", str(i - 1))
        
        ret.append(Str)

    return "\n".join(ret)


def CompileToSingleExpr(Stmts):
    ret = "$NEXT"
    for i in xrange(len(ArrayArgs)):
        CurStr = translator.toString(Stmts[1], ForceBracket=True) \
            .replace("$AELE", ArrayArgs[i]) \
            .replace("$AIDX", str(i)) \
            #.replace("$ANID", str(i + 1)) \
            #.replace("$APID", str(i - 1))
        ret = ret.replace("$NEXT", CurStr)
        #print(ret, CurStr)
    BoundStr = translator.toString(Stmts[0], ForceBracket=True)
    ret = ret.replace("$NEXT", BoundStr)
    return MakeDefineStr("", ret)


def Extend(Stmts, isTop=False):
    ret = []
    for i in xrange(len(Stmts)):
        if type(Stmts[i]) == list:
            TryExtend = Extend(Stmts[i])
            if len(TryExtend) > 0 :
                for extended in TryExtend:
                    ret.append(Stmts[0:i]+[extended]+Stmts[i+1:])
        elif Productions.has_key(Stmts[i]):
            for extended in Productions[Stmts[i]]:
                ret.append(Stmts[0:i] + [extended] + Stmts[i + 1:])
        if len(ret) > 0:
            return ret
    return ret

def stripComments(bmFile):
    noComments = '('
    for line in bmFile:
        line = line.split(';', 1)[0]
        noComments += line
    return noComments + ')'


if __name__ == '__main__':
    benchmarkFile = open(sys.argv[1])
    bm = stripComments(benchmarkFile)
    bmExpr = sexp.sexp.parseString(bm, parseAll=True).asList()[0] #Parse string to python list
    #pprint.pprint(bmExpr)
    checker=translator.ReadQuery(bmExpr)
    #print (checker.check('(define-fun f ((x Int)) Int (mod (* x 3) 10)  )'))
    #raw_input()
    SynFunExpr = []
    for expr in bmExpr:
        if len(expr)==0:
            continue
        elif expr[0]=='synth-fun':
            SynFunExpr=expr
    FuncDefine = ['define-fun'] + SynFunExpr[1:4]  #copy function signature
    #print(FuncDefine)
    
    FuncInvoke = [FuncDefine[1]]
    for argInfo in FuncDefine[2]:
        FuncInvoke.append(argInfo[0])
    #print(FuncInvoke)





    # 看参数列表名字，猜测是否接收数组为输入
    funcnum = re.findall(r'\d+', FuncDefine[1])
    argname = []
    for arg in SynFunExpr[2]:
        argname.append(arg[0])
    cpcnt = {}
    for i in argname:
        for j in argname:
            cp = ""
            for k in xrange(0, min(len(i), len(j))):
                if i[:k] == j[:k]:
                    cp = i[:k]
                else:
                    break
            if cpcnt.has_key(cp):
                cpcnt[cp] = cpcnt[cp] + 1
            else:
                cpcnt[cp] = 1
    cpcnt = sorted(cpcnt.items(), key=operator.itemgetter(1))
    cp = cpcnt[-1][0]

    if len(funcnum) > 0:
        num = int(funcnum[0])
        if num >= 3 and num == len(argname):
            ArrayMode = True
            ArrayArgs = argname
            OtherArgs = []
    if not ArrayMode and cp != "":
        for i in argname:
            if i.startswith(cp):
                ArrayArgs.append(i)
            else:
                OtherArgs.append(i)
        if len(ArrayArgs) > len(argname) / 2:
            ArrayMode = True
            ArrayArgs = natural_sort(ArrayArgs)
            OtherArgs = natural_sort(OtherArgs)
    if ArrayMode:
        #print "Array Input Detected!!!", "\nArray Args:", ArrayArgs, "\nOther Args:", OtherArgs
        pass
    else:
        ArrayArgs = [argname[0]]

    LoopBody = '#LOOPBODY'  #virtual starting symbol
    LoopBound = '#LOOPBOUND'
    
    BfsQueue = [[LoopBound, LoopBody]] #Top-down
    Productions = {LoopBody:[], LoopBound:[]}
    Type = {LoopBody:SynFunExpr[3],LoopBound:SynFunExpr[3]} # set starting symbol's return type

    for NonTerm in SynFunExpr[4]: #SynFunExpr[4] is the production rules
        NTName = NonTerm[0]
        NTType = NonTerm[1]
        if NTType == Type[LoopBody]:
            Productions[LoopBody].append(NTName)
            Productions[LoopBound].append(NTName)
        Type[NTName] = NTType
        #Productions[NTName] = NonTerm[2]
        Productions[NTName] = []
        for NT in NonTerm[2]:
            if type(NT) == tuple:
                Productions[NTName].append(str(NT[1])) # deal with ('Int',0). You can also utilize type information, but you will suffer from these tuples.
            else:
                Productions[NTName].append(NT)
    
    if ArrayMode:
        ArrayIdxs = list(map(str, range(0, len(ArrayArgs))))
        for p in Productions:
            Productions[p] = filter(lambda x: x not in ArrayArgs, Productions[p])
            Productions[p] = filter(lambda x: x not in ArrayIdxs, Productions[p])
        
        for StSym in Productions[LoopBody]:
            Productions[StSym].insert(0, ArrayArgs[0])
            Productions[StSym].append(ArrayArgs[-1])

        for StSym in Productions[LoopBody]:
            Productions[StSym].insert(1, "$NEXT") # 上一次循环结果
            Productions[StSym].insert(2, "$AELE")  # 数组中当前元素
            Productions[StSym].insert(3, "$AIDX")  # 数组中当前元素
            #Productions[StSym].insert(4, "$ANID")  # 数组中当前元素+1
            #Productions[StSym].insert(5, "$APID")  # 数组中当前元素-1

        # try reduce binary ops
        for NT in Productions:
            if Type[NT] == "Bool":
                bop = map(lambda x: x[0], Productions[NT])
                #print bop
                if ">=" in bop and "<" in bop:
                    bop.remove(">=")
                if "<=" in bop and ">" in bop:
                    bop.remove("<=")
                Productions[NT] = list(filter(lambda x: x[0] in bop, Productions[NT]))
    
    
    #pprint.pprint(Productions)
    #pprint.pprint(Type)

    FuncDefineStr = translator.toString(FuncDefine, ForceBracket=True)  # use Force Bracket = True on function definition. MAGIC CODE. DO NOT MODIFY THE ARGUMENT ForceBracket = True.
    FuncInvokeStr = translator.toString(FuncInvoke, ForceBracket=True)  # use Force Bracket = True on function definition. MAGIC CODE. DO NOT MODIFY THE ARGUMENT ForceBracket = True.

    while(len(BfsQueue)!=0):
        Curr = BfsQueue.pop(0)
        #print("Extending "+str(Curr))
        TryExtend = Extend(Curr)
        if(len(TryExtend)==0): # Nothing to extend
            Str = CompileToMultipleFunc(Curr)
            #print Str
            
            counterexample = checker.check(Str)
            #print counterexample
            if (counterexample == None):  # No counter-example
                #print "=======  SOLUTION FOUND  ======="
                #print Str
                Ans = CompileToSingleExpr(Curr)
                #print "Compiled to " + str(len(Ans)) + " bytes"
                assert checker.check(Str) == None
                break
            #print '2'
        #print(TryExtend)
        #raw_input()
        #BfsQueue+=TryExtend

        TryExtend = filter(lambda x: IsLegal(x), TryExtend)
        #print "TryExtend =", TryExtend
        #raw_input()
        TE_set = set()
        for TE in TryExtend:
            TE_str = str(TE)
            if not TE_str in TE_set:
                BfsQueue.append(TE)
                TE_set.add(TE_str)

    #评测机有bug，若输出太长会阻塞，为此把stdout的管道缓冲大小调大一些解决这个问题
    if len(Ans) > 2000:
        try:
            fcntl.fcntl(1, 1031, len(Ans) + 100)  # 1031=F_SETPIPE_SZ
        except:
            pass

    print(Ans)

	# Examples of counter-examples    
	# print (checker.check('(define-fun max2 ((x Int) (y Int)) Int 0)'))
    # print (checker.check('(define-fun max2 ((x Int) (y Int)) Int x)'))
    # print (checker.check('(define-fun max2 ((x Int) (y Int)) Int (+ x y))'))
    # print (checker.check('(define-fun max2 ((x Int) (y Int)) Int (ite (<= x y) y x))'))
