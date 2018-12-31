# 软件分析技术 2018 课程大作业二
## Syntax-Guided Program Synthesize
### 小组成员： 黄杨洋 张博洋 刘渊强
### 一、 目标：给定文法 G 和约束 C ，生成程序 P 使得 P 属于 L(G) 并且 P 满足约束 C
* 文法 G 的形式为 Synth-lib
* 约束 C 的形式为 SMTlib
* 输出 P 的形式为 SMTlib
* 基于课程上给的Python框架
* 使用 z3 作为 checker
### 二、 代码目录及评测结果
* 主要代码实现在 `programs/baseline/main.py` 中
* 单点评测： `python programs/baseline/main.py tests/open_tests/[file].sl`
* 评测机： `python test.py`
* 评测结果： 在本机评测中，已通过 `open_tests` 中的 `three.sl` `tutorial.sl` `max*.sl`(所有max类型) `array_search_*.sl`(除array_search_2.sl外均已通过)
* 尚未通过的为 `array_search_2` `s1` `s2` `s3` 这四个测试
* 具体评测结果见附录
### 三、 算法主要设计思想及代码实现
* 

### 四、 小组
* 黄杨洋 1801213684
* 张博洋 1801111368
* 刘渊强 1500012883
### 附录：具体评测结果（仅供参考）
* 评测环境：
  * OS : Ubuntu 18.04.1 LTS
  * Memory : 15.6GiB
  * Processor : Intel® Core™ i7-7700HQ CPU @ 2.80GHz × 8 
  * OS type : 64-bit
* 详细评测结果(Passed)：

| file | time | file | time |
|------|------|------|------|
| three.sl| 0.828398 | tutorial.sl | 15.028949 |
| max2.sl | 8.121671 | array_search_3.sl | 7.379524 |
| max3.sl | 7.198264 | array_search_4.sl | 7.385054 |
| max4.sl | 8.027599 | array_search_5.sl | 13.321703 |
| max5.sl | 7.837716 | array_search_6.sl | 14.576616 |
| max6.sl | 10.338283 | array_search_7.sl | 16.380970 |
| max7.sl | 8.928699 | array_search_8.sl | 12.795453 |
| max8.sl | 11.801412 | array_search_9.sl | 15.346137 |
| max9.sl | 13.937693 | array_search_10.sl | 14.742849 |
| max10.sl | 9.805644 | array_search_11 | 15.811373 |
| max_11.sl | 10.154794 | array_search_12.sl | 24.047682 |
| max12.sl | 12.285507 | array_search_13.sl | 23.894458 |
| max13.sl | 19.011390 | array_search_14.sl | 20.825436 |
| max14.sl | 11.604948 | array_search_15.sl | 28.895348 |
| max15.sl | 13.603447 |    |    |