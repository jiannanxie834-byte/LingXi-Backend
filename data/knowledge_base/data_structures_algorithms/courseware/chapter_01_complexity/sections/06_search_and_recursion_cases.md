# 1.6 复杂度分析案例：线性查找、二分查找与递归初步

## 学习目标
通过线性查找、二分查找和简单递归，把前面学到的复杂度概念落实到具体代码片段中。

## 核心讲解
线性查找会从头到尾检查元素，目标越靠后，检查次数越多；目标不存在时需要看完整个数组。二分查找要求数据有序，每次比较后都能排除一半区间，因此增长很慢。递归复杂度要同时看每层做多少工作，以及问题规模如何缩小。

```python
def linear_search(a, target):
    for i, x in enumerate(a):
        if x == target:
            return i
    return -1
```
线性查找最坏情况是 O(n)，额外空间是 O(1)。

```python
def binary_search(a, target):
    left, right = 0, len(a) - 1
    while left <= right:
        mid = (left + right) // 2
        if a[mid] == target:
            return mid
        if a[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```
二分查找每轮把区间约减半，时间复杂度是 O(log n)，额外空间是 O(1)。

## 简短例子
递归求数组和时，如果每次处理一个元素并递归到下一个位置，总层数是 n，每层做常数工作，时间是 O(n)，调用栈空间也是 O(n)。

## 常见误区
二分查找必须依赖有序数据；递归不是自动更快，递归层数和每层工作量都要分析。

## 与后续学习的关系
这些案例会连接第 2 章的线性结构和第 3 章递归思想，是后续刷题与代码实验的分析模板。
