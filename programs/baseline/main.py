
# -*- coding: utf-8 -*-
import sys
import sexp
import pprint
import translator
import operator



ArrayArgs = []
OtherArgs = []
ArrayMode = False

Productions = None
Type = None


def AIsLegal(Stmts, inFor=False, forCnt=0):
    for i in xrange(len(Stmts)):
        if type(Stmts[i]) == list:
            if not AIsLegal(Stmts[i], inFor, forCnt):
                #print "not legal:", Stmts
                return False
        else:
            if Stmts[i] == "$FOR":
                if inFor or forCnt > 0:
                    return False
                inFor = True
                forCnt = forCnt + 1
            elif (not inFor) and (Stmts[i] == "$PREV" or Stmts[i] == "$CURR" or Stmts[i] == "$IDX"):
                #print "not in for:", Stmts[i]
                return False
            elif inFor and (Stmts[i] == "#FOR" or Stmts[i] == "$FOR"):
                #print "multiple for:", Stmts[i]
                return False
    return True

def ACompile(Stmts, forExpr=None, arIndex=0):
    #print "ACompile", Stmts, forExpr, arIndex
    
    
    result = []
    for i in xrange(len(Stmts)):
        if type(Stmts[i]) == list:
            result.append(ACompile(Stmts[i], forExpr, arIndex))
        else:
            if i == 0 and Stmts[i] == "$FOR":
                result.append(ACompile(Stmts[1:], Stmts, arIndex))
                break
            else:
                if forExpr is None:
                    result.append(Stmts[i])
                else:
                    if Stmts[i] == "$CURR":
                        result.append(ArrayArgs[arIndex])
                    elif Stmts[i] == "$IDX":
                        result.append(str(arIndex))
                    elif Stmts[i] == "$PREV":
                        if arIndex < len(ArrayArgs) - 1:
                            result.append(ACompile(forExpr[1:], forExpr, arIndex + 1))
                        else:
                            result.append(ArrayArgs[-1])
                    else:
                        result.append(Stmts[i])
    #print Stmts, "=>", result
    return result

def Extend(Stmts):
    ret = []

    if ArrayMode:
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
                break
    else:
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
                break
    
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
    StartSym = 'My-Start-Symbol' #virtual starting symbol
    for expr in bmExpr:
        if len(expr)==0:
            continue
        elif expr[0]=='synth-fun':
            SynFunExpr=expr
    FuncDefine = ['define-fun']+SynFunExpr[1:4] #copy function signature
    #print(FuncDefine)
    


    # 看参数列表名字，猜测是否接收数组为输入
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
    if cp != "":
        for i in argname:
            if i.startswith(cp):
                ArrayArgs.append(i)
            else:
                OtherArgs.append(i)
        if len(ArrayArgs) > len(argname) / 2:
            ArrayMode = True
            ArrayArgs = sorted(ArrayArgs)
            OtherArgs = sorted(OtherArgs)
    if ArrayMode:
        print "Array Input Detected!", ArrayArgs, OtherArgs
    




    BfsQueue = [[StartSym]] #Top-down
    Productions = {StartSym:[]}
    Type = {StartSym:SynFunExpr[3]} # set starting symbol's return type

    for NonTerm in SynFunExpr[4]: #SynFunExpr[4] is the production rules
        NTName = NonTerm[0]
        NTType = NonTerm[1]
        if NTType == Type[StartSym]:
            Productions[StartSym].append(NTName)
        Type[NTName] = NTType
        #Productions[NTName] = NonTerm[2]
        Productions[NTName] = []
        for NT in NonTerm[2]:
            if type(NT) == tuple:
                Productions[NTName].append(str(NT[1])) # deal with ('Int',0). You can also utilize type information, but you will suffer from these tuples.
            else:
                Productions[NTName].append(NT)

    if ArrayMode:
        for StSym in Productions[StartSym]:
            Productions[StSym].insert(0, "#FOR")
            Productions[StSym].insert(1, "$PREV") # 上一次循环结果
            Productions[StSym].insert(2, "$CURR")  # 数组中当前元素
            #Productions[StSym].insert(2, "$IDX")  # 当前下标
            
        Productions["#FOR"] = [["$FOR", StartSym]]
        for p in Productions:
            Productions[p] = filter(lambda x: x not in ArrayArgs, Productions[p])
        
        BfsQueue = [["#FOR"]]

    print(Productions)
    print(Type)


    Count = 0
    while(len(BfsQueue)!=0):
        Curr = BfsQueue.pop(0)
        #print("Extending "+str(Curr))
        TryExtend = Extend(Curr)
        if ArrayMode:
            TryExtend = filter(lambda x: AIsLegal(x), TryExtend)
        #print("TryExtend="+str(TryExtend))
        if (len(TryExtend) == 0):  # Nothing to extend
            BCurr = Curr
            if ArrayMode:
                print "Before Compile:", Curr
                #assert AIsLegal(Curr)
                Curr = ACompile(Curr)
                #print "After Compiled: ", Curr

            FuncDefineStr = translator.toString(FuncDefine,ForceBracket = True) # use Force Bracket = True on function definition. MAGIC CODE. DO NOT MODIFY THE ARGUMENT ForceBracket = True.
            CurrStr = translator.toString(Curr)
            #SynFunResult = FuncDefine+Curr
            #Str = translator.toString(SynFunResult)
            Str = FuncDefineStr[:-1]+' '+ CurrStr+FuncDefineStr[-1] # insert Program just before the last bracket ')'
            #Str = "(define-fun f ((x Int)) Int (ite (<= x 5) (* x 10) x))"
            Count += 1
            # print (Count)
            #print (Str)
            # if Count % 100 == 1:
                # print (Count)
                # print (Str)
                #raw_input()
            #print '1'
            counterexample = checker.check(Str)
            #print counterexample
            if (counterexample == None):  # No counter-example
                print(BCurr)
                Ans = Str
                break
            #print '2'
        
        #raw_input()
        #BfsQueue+=TryExtend
        TE_set = set()
        for TE in TryExtend:
            TE_str = str(TE)
            if not TE_str in TE_set:
                BfsQueue.append(TE)
                TE_set.add(TE_str)

    print(Ans)

	# Examples of counter-examples    
	# print (checker.check('(define-fun max2 ((x Int) (y Int)) Int 0)'))
    # print (checker.check('(define-fun max2 ((x Int) (y Int)) Int x)'))
    # print (checker.check('(define-fun max2 ((x Int) (y Int)) Int (+ x y))'))
    # print (checker.check('(define-fun max2 ((x Int) (y Int)) Int (ite (<= x y) y x))'))
