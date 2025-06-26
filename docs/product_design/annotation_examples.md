# 标注示例与操作指南

## 1. 标注任务概述

### 1.1 任务类型
基于OCR预处理的英文票据文档，进行敏感实体识别和分类标注，支持数据脱敏模型训练。

### 1.2 标注目标
识别文档中的所有敏感实体（包括被`[MASK]`遮挡的和未遮挡的），为每个敏感实体分配正确的类别标签。

## 2. 完整标注示例

### 2.1 发票类文档示例 (Invoice Demo)

#### 原始输入文档
```
From: 
[MASK_[MASK_Heather] [MASK_Hatfield]] 
INVOICE 
 
Business Name: 
[MASK_[MASK_Heather] [MASK_Hatfield]] 
[MASK_[MASK_36441] [MASK_Phillips Underpass] Suite 106] 
[MASK_New Daniel], [MASK_MT] [MASK_49458] 
 
INVOICE # 
T96087065 
 
DATE 
[MASK_05/06/2022] 
 
DUE DATE 
[MASK_05/06/2022] 

Bill to: 
Wilson, Taylor and Kim and Sons 
TOTAL AMOUNT 
4382.93 
 
[MASK_[MASK_Brittney] [MASK_Alvarado]] 
USNS Palmer 
FPO AE 79899 
TOTAL DUE 
4382.93 
```

#### 标注任务界面展示
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 任务 #001 - invoice_001.txt                   [15/100]   │
│ [保存] [提交] [跳过] [帮助]                                  │
├─────────────────┬───────────────────────────────────────────┤
│ 🎯 标注指令      │ 📄 文档内容                              │
│                 │                                           │
│ 找出文档中的敏感  │ From:                                    │
│ 实体并分类标注。  │ [MASK_[MASK_Heather] [MASK_Hatfield]]   │
│                 │ INVOICE                                   │
│ 需要标注的类别： │                                           │
│ 1.人名相关       │ Business Name:                           │
│ 2.地址相关       │ [MASK_[MASK_Heather] [MASK_Hatfield]]   │
│ 3.证件号码       │ [MASK_[MASK_36441] [MASK_Phillips...]]   │
│ 4.时间和联系信息  │ [MASK_New Daniel], [MASK_MT] [MASK_...] │
│                 │                                           │
│ [查看详细说明]   │ Bill to: Wilson, Taylor and Kim and Sons │
├─────────────────┼───────────────────────────────────────────┤
│ 🏷️ 实体分类     │ ✅ 当前标注结果                          │
│                 │                                           │
│ 👤 人名相关      │ • Heather Hatfield: FullName     [删除] │
│ • FullName      │ • Heather: FirstName             [删除] │
│ • FirstName     │ • Hatfield: LastName             [删除] │
│ • LastName      │ • Brittney Alvarado: FullName    [删除] │
│                 │ • Brittney: FirstName            [删除] │
│ 🏠 地址相关      │ • Alvarado: LastName             [删除] │
│ • Address       │ • Wilson, Taylor and Kim and Sons:       │
│ • StreetNumber  │   CompanyName                    [删除] │
│ • StreetName    │ • 36441 Phillips Underpass Suite 106:   │
│ • City         │   Address                        [删除] │
│ • State        │ • 36441: StreetNumber            [删除] │
│ • ZipCode      │ • Phillips Underpass: StreetName [删除] │
│                 │ • New Daniel: City               [删除] │
│ 📄 证件号码      │ • MT: State                      [删除] │
│ • InvoiceNumber │ • 49458: ZipCode                 [删除] │
│ • CompanyName   │ • T96087065: InvoiceNumber       [删除] │
│                 │ • USNS Palmer: MilitaryAddress   [删除] │
│ 🕐 时间信息      │ • FPO AE 79899: MilitaryAddress  [删除] │
│ • Date         │ • 05/06/2022: Date               [删除] │
│                 │                                           │
│                 │ 📊 统计: 共标注 15 个实体                │
└─────────────────┴───────────────────────────────────────────┘
```

#### 预期标注结果
```
实体清单（冒号后的标签请查表）
----------------------------------------------------------
Heather Hatfield: FullName
Heather: FirstName
Hatfield: LastName
36441 Phillips Underpass Suite 106: Address
36441: StreetNumber
Phillips Underpass: StreetName
New Daniel: City
MT: State
49458: ZipCode
Brittney Alvarado: FullName
Brittney: FirstName
Alvarado: LastName
Wilson, Taylor and Kim and Sons: CompanyName
T96087065: InvoiceNumber
05/06/2022: Date
USNS Palmer: MilitaryAddress
FPO AE 79899: MilitaryAddress
```

### 2.2 工资单类文档示例 (Payroll Demo)

#### 原始输入文档
```
DOUBLE R BRAND FOODS LLC                                    
[MASK_800 ELLEN TROUT DRIVE]                   
[MASK_LUFKIN], TEXAS [MASK_75904]                     

PAY $501.33
To the order of:
[MASK_[MASK_LADISLADA] [MASK_ANDRADE]]
[MASK_443 DOUBLE TREE]               
[MASK_LUFKIN], [MASK_TX] [MASK_75904]

Date: [MASK_12/06/2019]
Earnings Statement
Pay Period: 11/27/2019 to 12/03/2019
Paycheck Date: [MASK_12/06/2019]
Paycheck Number: 0000103580
```

#### 预期标注结果
```
实体清单（冒号后的标签请查表）
----------------------------------------------------------
LADISLADA ANDRADE: FullName
LADISLADA: FirstName
ANDRADE: LastName
800 ELLEN TROUT DRIVE: Address
LUFKIN: City
TX: State
75904: ZipCode
443 DOUBLE TREE: Address
12/06/2019: Date
DOUBLE R BRAND FOODS LLC: CompanyName
0000103580: CheckNumber
```

## 3. 标注操作流程

### 3.1 标注前准备
1. **任务接收**: 系统自动分配或手动选择任务
2. **指令阅读**: 仔细阅读左上角的标注指令
3. **文档预览**: 快速浏览整个文档内容，了解文档类型

### 3.2 实体识别步骤

#### 步骤1: 扫描MASK内容
```
原文: [MASK_[MASK_Heather] [MASK_Hatfield]]
识别: Heather Hatfield (完整姓名)
分解: Heather (名), Hatfield (姓)
```

#### 步骤2: 识别未遮挡敏感信息
```
原文: Wilson, Taylor and Kim and Sons
识别: 公司名称
分类: CompanyName
```

#### 步骤3: 复合实体处理
```
原文: [MASK_[MASK_36441] [MASK_Phillips Underpass] Suite 106]
完整地址: 36441 Phillips Underpass Suite 106
分解标注:
- 36441 Phillips Underpass Suite 106: Address
- 36441: StreetNumber  
- Phillips Underpass: StreetName
```

### 3.3 分类标注规则

#### 人名相关实体
- **FullName**: 完整的人名 (如: Heather Hatfield)
- **FirstName**: 名字 (如: Heather)
- **LastName**: 姓氏 (如: Hatfield)
- **MiddleName**: 中间名 (如适用)

#### 地址相关实体
- **Address**: 完整地址 (如: 36441 Phillips Underpass Suite 106)
- **StreetNumber**: 街道号码 (如: 36441)
- **StreetName**: 街道名称 (如: Phillips Underpass)
- **City**: 城市 (如: New Daniel)
- **State**: 州/省 (如: MT, TX)
- **ZipCode**: 邮政编码 (如: 49458)
- **Country**: 国家 (如: USA)

#### 证件号码类
- **InvoiceNumber**: 发票号 (如: T96087065)
- **CheckNumber**: 支票号 (如: 0000103580)
- **CompanyName**: 公司名称 (如: Wilson, Taylor and Kim and Sons)
- **IDNumber**: 身份证号
- **PassportNumber**: 护照号
- **DriversLicense**: 驾照号

#### 时间和联系信息
- **Date**: 日期 (如: 05/06/2022, 12/06/2019)
- **Time**: 时间
- **PhoneNumber**: 电话号码
- **Email**: 电子邮件
- **IPAddress**: IP地址

#### 特殊地址类型
- **MilitaryAddress**: 军事地址 (如: USNS Palmer, FPO AE 79899)

## 4. 质量标准

### 4.1 完整性要求
- ✅ 识别所有被MASK的敏感实体
- ✅ 发现文档中其他潜在的敏感信息
- ✅ 不遗漏任何明显的敏感数据

### 4.2 准确性要求
- ✅ 实体文本提取准确，不多不少
- ✅ 分类标签选择正确
- ✅ 复合实体正确分解

### 4.3 一致性要求
- ✅ 相同类型实体使用统一标签
- ✅ 分解粒度保持一致
- ✅ 命名规范统一

## 5. 常见错误与避免

### 5.1 遗漏错误
❌ **错误**: 只标注被MASK的内容，忽略未遮挡的敏感信息
```
遗漏: Wilson, Taylor and Kim and Sons (CompanyName)
```
✅ **正确**: 同时标注MASK和非MASK的敏感实体

### 5.2 分类错误
❌ **错误**: 将完整地址标注为City
```
错误: 36441 Phillips Underpass Suite 106: City
```
✅ **正确**: 正确识别为完整地址
```
正确: 36441 Phillips Underpass Suite 106: Address
```

### 5.3 分解错误
❌ **错误**: 不完整的分解
```
遗漏: 只标注 Heather Hatfield: FullName
```
✅ **正确**: 完整分解
```
正确: 
Heather Hatfield: FullName
Heather: FirstName
Hatfield: LastName
```

## 6. 特殊情况处理

### 6.1 嵌套MASK处理
```
原文: [MASK_[MASK_Heather] [MASK_Hatfield]]
处理: 识别内层实体 Heather, Hatfield 和外层组合 Heather Hatfield
```

### 6.2 军事地址处理
```
原文: USNS Palmer / FPO AE 79899
标注: 
- USNS Palmer: MilitaryAddress
- FPO AE 79899: MilitaryAddress
```

### 6.3 公司名称识别
```
原文: Wilson, Taylor and Kim and Sons
识别: 含有连词and的完整公司名称
标注: Wilson, Taylor and Kim and Sons: CompanyName
```

## 7. 验收检查清单

### 标注完成前自检
- [ ] 所有MASK内容都已识别并标注
- [ ] 检查是否有遗漏的未MASK敏感信息
- [ ] 验证所有分类标签选择正确
- [ ] 确认复合实体已正确分解
- [ ] 检查实体文本提取的准确性
- [ ] 确保标注格式符合要求

### 提交前最终确认
- [ ] 标注实体数量合理（通常10-20个）
- [ ] 没有重复或冲突的标注
- [ ] 所有标注都有明确的业务意义
- [ ] 标注结果可以支持数据脱敏需求 