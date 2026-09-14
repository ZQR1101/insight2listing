# Insight2Listing 详细产品与技术方案

> 面向 Amazon 美国站热门日用消费品的评论洞察、选品验证与智能上新 Agent

- 文档版本：1.0
- 编制日期：2026-09-14
- 项目性质：个人开源项目
- 开源许可证：MIT
- 首发平台：Amazon 美国站
- 产品形态：结构化工作流系统，聊天作为辅助能力
- 部署策略：自托管优先，托管就绪
- 界面语言：简体中文、English

---

## 1. 执行摘要

Insight2Listing 是一套面向跨境电商运营人员和中小卖家的 AI 工作流系统。系统接收用户有权使用的商品、竞品、价格、评论和趋势数据，从中识别市场需求、用户痛点和竞品缺口，生成可追溯的“商品机会卡”，再依据经过确认的商品事实，生成 Amazon 美国站 Listing、图片创意方案和商品视觉素材。

项目整合两个业务场景：

1. **AI 市场洞察与选品验证**：分析候选商品的需求信号、竞品表现、评论痛点和差异化空间；
2. **AI 智能上新**：生成标题、五点描述、产品描述、搜索词、主图处理方案、详情图和内容检查报告。

系统不将生成式 AI 视为“自动写文案工具”，而是建立以下闭环：

```text
候选商品与市场数据
        ↓
数据校验与来源记录
        ↓
评论洞察与竞品缺口
        ↓
商品机会卡
        ↓
人工确认商品事实
        ↓
Listing 与视觉素材生成
        ↓
事实、图片与平台规则检查
        ↓
人工审核与导出
```

第一阶段不依赖卖家授权账号，不自动抓取 Amazon 网页，也不直接发布商品。Amazon SP-API 真实账号授权、生产数据同步和后台自动上架放到后续 Beta 阶段。

---

## 2. 项目愿景

### 2.1 愿景

让跨境电商的市场洞察、商品定位、内容制作和审核形成一条有证据、可追溯、可复现的智能工作流。

### 2.2 核心价值

- 将分散评论转化为结构化需求；
- 将市场需求转化为可执行的商品差异化方向；
- 将商品差异化方向转化为受事实约束的 Listing；
- 将卖点和商品事实转化为可审核的图片创意；
- 让每项洞察和卖点能够追溯到数据来源；
- 在缺失数据时明确表达不确定性，而不是由模型补全事实。

### 2.3 产品承诺

产品可以承诺：

- 提高评论整理与 Listing 初稿制作效率；
- 提供带证据的消费者需求洞察；
- 降低未经确认的商品声明进入 Listing 的概率；
- 生成以转化为目标的商品内容与视觉方案；
- 帮助用户发现需要人工判断的数据缺口和风险。

产品不应承诺：

- 保证选出爆款；
- 保证销量或转化率增长；
- 根据评论准确预测未来销量；
- 在没有成本数据时准确估算利润；
- 在没有真实商品图时准确生成可直接上架的主图；
- 在未经人工审核的情况下自动发布商品。

---

## 3. 产品定位与边界

### 3.1 第一阶段定位

第一阶段定位为：

> **AI 候选商品验证、评论洞察与 Listing 生成系统。**

用户提供一个或多个候选商品，系统帮助判断：

- 哪些需求信号值得关注；
- 消费者主要抱怨什么；
- 哪些问题跨多个竞品反复出现；
- 现有竞品在哪些方面没有满足消费者；
- 什么差异化卖点具有数据依据；
- 现有商品事实是否足以支持这些卖点；
- 如何将已确认卖点转化为 Amazon Listing 与图片方案。

### 3.2 后续市场机会发现

完整的自动选品需要从更大范围的候选池中发现商品机会。后续版本可通过官方接口、第三方数据连接器和用户自有数据形成分层漏斗：

```text
类目、榜单与搜索趋势
        ↓
候选商品池
        ↓
需求、竞争、风险初筛
        ↓
候选商品排序
        ↓
竞品与评论深度分析
        ↓
商品机会卡
```

系统不需要穷举整个 Amazon 市场，但必须明确候选池覆盖范围、数据来源与截至时间。

### 3.3 首发平台边界

- 目标平台：Amazon.com；
- 目标市场：美国；
- Listing 语言：英文；
- 界面语言：中英文；
- 币种：USD；
- 第一阶段输出：文案、视觉素材和导出包；
- 第一阶段不直接调用 Amazon 上架接口。

### 3.4 首批测试商品

| 商品 | 代表性 | 主要可分析问题 |
|---|---|---|
| 压缩旅行收纳袋 | 趋势型旅行用品 | 拉链、容量、压缩效果、重量和耐用性 |
| 玻璃喷油壶 | 热门厨房用品 | 漏油、喷雾均匀度、堵塞、玻璃强度和食品接触声明 |
| 车载垃圾桶 | 汽车日用品 | 固定方式、防漏、容量、开口设计和车型适配 |

三个商品用于验证跨品类能力，不构成商业投资或真实选品建议。

---

## 4. 目标用户与使用场景

### 4.1 核心用户

- 中小型跨境电商卖家；
- Amazon 选品和运营人员；
- 商品开发人员；
- 国内外贸企业与供应商；
- Listing 文案与视觉设计人员；
- 希望建立标准化上新流程的个人卖家。

### 4.2 用户故事

#### 候选商品验证

> 作为选品人员，我希望导入几个候选商品及竞品数据，让系统指出需求信号、主要风险和数据缺口，帮助我决定哪个商品值得继续调研。

#### 评论洞察

> 作为运营人员，我希望系统从多语言评论中识别高频痛点，并能查看支持每个结论的评论证据。

#### Listing 生成

> 作为 Listing 编辑人员，我希望根据已确认的商品事实和用户痛点生成英文标题、五点描述与搜索词，同时避免 AI 编造功能。

#### 图片生成

> 作为视觉设计人员，我希望系统根据真实商品图和卖点生成场景图、功能图和详情页素材，并标出商品外观或平台规则风险。

#### 辅助聊天

> 作为使用者，我希望追问系统为什么推荐某个痛点、要求它缩小时间范围或重新生成某段内容，但不希望关键信息只存在聊天记录中。

---

## 5. 产品设计原则

1. **工作流优先**：主要任务通过结构化页面与状态完成；
2. **聊天辅助**：聊天用于解释、筛选、修改和导航，不代替数据结构；
3. **证据优先**：洞察、建议与卖点必须携带来源；
4. **事实隔离**：消费者需求不等于商品已有能力；
5. **人在回路**：商品事实、风险卖点、图片和最终导出由人确认；
6. **不确定性可见**：缺失数据、低样本量和低置信度必须明确展示；
7. **来源可追溯**：记录数据来源、采集或导入时间与许可范围；
8. **模型可替换**：文本、图像和嵌入模型不与业务逻辑绑定；
9. **默认安全**：不内置违规抓取，不在前端暴露 API Key；
10. **国际化优先**：界面和生成内容从第一版支持多语言结构。

---

## 6. 信息架构与页面

### 6.1 项目中心

- 新建分析项目；
- 设置站点、类目、目标语言和币种；
- 查看工作流状态；
- 查看数据截至时间；
- 查看任务成本和失败记录；
- 恢复未完成任务。

### 6.2 数据导入中心

- 上传 CSV、JSON、XLSX；
- 选择数据类型；
- 自动识别字段；
- 手动映射字段；
- 预览数据；
- 展示格式错误、缺失字段和重复记录；
- 记录来源、许可和用户确认；
- 生成导入报告。

### 6.3 候选商品看板

- 商品、价格、评分和评论数量对比；
- 数据完整度；
- 数据新鲜度；
- 初步机会分；
- 风险和缺失数据；
- 候选商品排序；
- 进入深度分析。

### 6.4 评论洞察页

- 正负面主题；
- 高频痛点；
- 使用场景；
- 购买动机；
- 星级影响；
- 时间趋势；
- 跨竞品普遍性；
- 代表性证据；
- 主题合并与拆分；
- 接受、拒绝或编辑洞察。

### 6.5 商品机会卡

- 目标人群；
- 使用场景；
- 核心痛点；
- 评论证据；
- 竞品缺口；
- 差异化方向；
- 关键词；
- 机会评分；
- 数据置信度；
- 缺失维度；
- 风险提示；
- 待确认商品事实。

### 6.6 商品事实中心

- 材质；
- 尺寸；
- 重量；
- 容量；
- 配件；
- 颜色和变体；
- 使用限制；
- 检测或认证；
- 商品图片；
- 事实来源与确认状态。

### 6.7 Listing 工作台

- 生成标题；
- 生成五点描述；
- 生成产品描述；
- 生成搜索词；
- 中英文对照；
- 事实来源标记；
- 版本对比；
- 局部重新生成；
- 平台规则检查；
- 人工编辑与批准。

### 6.8 视觉创意工作台

- 上传真实商品图；
- 图片质量检查；
- 生成 Creative Brief；
- 选择图片类型；
- 生成多个视觉版本；
- 商品一致性检查；
- 确定性文字排版；
- 平台规则检查；
- 人工审核与导出。

### 6.9 辅助聊天侧栏

聊天可执行：

- 解释某项评分；
- 引用相关证据；
- 修改筛选条件；
- 调整文案语气；
- 创建新版本；
- 导航到相关页面；
- 发起受控工作流操作。

聊天不得绕过：

- 商品事实确认；
- 风险声明；
- 图片审核；
- 导出前审核；
- 外部发布授权。

---

## 7. 核心工作流

### 7.1 工作流状态

```text
DRAFT
  ↓
DATA_IMPORTED
  ↓
DATA_VALIDATED
  ↓
INSIGHTS_GENERATED
  ↓
INSIGHTS_REVIEWED
  ↓
PRODUCT_FACTS_CONFIRMED
  ↓
LISTING_GENERATED
  ↓
CREATIVES_GENERATED
  ↓
COMPLIANCE_CHECKED
  ↓
READY_FOR_EXPORT
  ↓
EXPORTED
```

### 7.2 状态设计要求

每一步保存：

- 输入快照；
- 输出快照；
- 数据版本；
- 模型和提示词版本；
- 任务状态；
- 错误类型；
- 重试次数；
- 估算与实际费用；
- 人工确认记录；
- 创建和完成时间。

### 7.3 不可绕过的确认点

1. 用户确认采用哪些洞察；
2. 用户确认商品真实参数；
3. 用户确认图片没有改变商品结构和配件；
4. 用户确认最终 Listing 与导出包；
5. 后续自动上架功能必须单独确认。

---

## 8. 数据策略

### 8.1 双数据轨道

#### 实时业务数据

用于真实项目分析：

- 当前商品属性；
- 当前价格和 Offer；
- 当前销售排名；
- 近期评论主题；
- 搜索趋势；
- 用户自有商品事实。

#### 固定评测数据

用于回归评测：

- 冻结的数据快照；
- 固定的商品事实；
- 固定的评论或主题；
- 固定的基线提示词；
- 固定的预期检查结果；
- 人工核验记录。

产品运行需要新数据，Agent 回归测试需要可复现数据，二者不可混用。

### 8.2 数据来源层级

| 层级 | 来源 | 是否依赖卖家授权 |
|---|---|---:|
| L0 | 合成演示与测试数据 | 否 |
| L1 | 用户上传 CSV、JSON、XLSX | 否 |
| L2 | 用户配置的第三方数据源 | 否 |
| L3 | Amazon SP-API 官方连接器 | 是 |

### 8.3 第一阶段数据入口

第一阶段完整支持：

- CSV；
- JSON；
- XLSX；
- REST API 导入接口；
- 合成演示数据；
- 固定评测快照。

第一阶段预留但不依赖：

- Amazon Catalog Items API；
- Amazon Product Pricing API；
- Amazon Customer Feedback API；
- Google Trends；
- 第三方价格和排名数据服务。

### 8.4 数据适配架构

```text
CSV ─────┐
JSON ────┤
XLSX ────┼─→ Source Adapter → Validation → Canonical Schema
REST API ┤
SP-API ──┤
第三方API ┘
```

每个适配器只负责：

- 读取来源格式；
- 映射字段；
- 保留原始标识；
- 输出统一 Schema；
- 生成错误报告；
- 记录来源和新鲜度。

业务模块不直接读取外部平台原始格式。

### 8.5 数据新鲜度

每个市场数据字段至少携带：

```json
{
  "value": 19.99,
  "source": "user_import",
  "observed_at": "2026-09-14T08:00:00Z",
  "source_updated_at": null,
  "freshness_status": "unknown",
  "license_ref": "user_attested",
  "raw_payload_hash": "sha256:..."
}
```

`freshness_status` 可取：

```text
fresh
aging
stale
unknown
```

建议刷新策略：

| 数据 | 产品建议刷新频率 |
|---|---|
| 当前价格和 Offer | 6～24小时 |
| 销售排名 | 每日 |
| 商品属性 | 每周或发生变化时 |
| 评论主题 | 每周 |
| 搜索趋势 | 每日或每周 |
| 平台规则 | 定期检查并版本化 |

刷新频率属于产品策略，不代表外部数据源保证相同更新速度。

### 8.6 Amazon 官方数据能力

Amazon Catalog Items API 可以提供商品属性、图片、商品类型、变体和销售排名等目录信息；Product Pricing API 用于价格和 Offer；Customer Feedback API 可以提供评论主题、提及数量、对星级的影响、趋势和评论片段，并在美国站可用。

第一阶段只开发连接器接口、Mock 与沙箱测试。真实卖家 OAuth 授权和生产环境验证放到后续 Beta。

参考：

- [Amazon Catalog Items API](https://developer-docs.amazon.com/sp-api/docs/catalog-items-api-v2022-04-01-reference)
- [Amazon Product Pricing API](https://developer-docs.amazon.com/sp-api/docs/product-pricing-api-v0-use-case-guide)
- [Amazon Customer Feedback API](https://developer-docs.amazon.com/sp-api/docs/customer-feedback-api)
- [Amazon SP-API 开发测试工具](https://developer-docs.amazon.com/sp-api/docs/development-tools)

### 8.7 数据许可原则

非商业项目不自动获得抓取、复制或重新分发平台数据的权利。

第一阶段：

- 不内置 Amazon 网页爬虫；
- 不绕过验证码、登录或访问限制；
- 不在 GitHub 分发完整 Amazon 评论数据；
- 不提交第三方商品图片和品牌资产；
- 仓库只提供合成数据或具有明确许可的数据；
- 用户导入前确认拥有相应处理权；
- 数据来源、许可和用途范围必须可记录。

Amazon 的部分数据接口和内容许可具有特定准入与用途限制，接入前需要针对具体来源审查协议：

- [Amazon Creators API Onboarding](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding)
- [Amazon Associates Program IP License](https://affiliate-program.amazon.com/help/operating/policies)

### 8.8 数据来源记录

每批数据保存：

```text
source_type
source_name
source_url
license
usage_scope
observed_at
imported_at
expires_at
user_attested
raw_payload_hash
```

---

## 9. 评论分析与证据系统

### 9.1 处理流程

```text
格式校验
→ 去重
→ 语言识别
→ 低质量和无关内容过滤
→ 主题分类
→ 情感与严重度分析
→ 语义聚类
→ 跨竞品合并
→ 证据绑定
→ 人工复核
```

### 9.2 支持的证据类型

```text
raw_review
review_excerpt
aggregated_topic
trend_metric
product_attribute
price_observation
sales_rank_observation
user_confirmed_fact
```

### 9.3 洞察状态

```text
generated
accepted
edited
rejected
superseded
```

### 9.4 防止错误归纳

- 每项洞察必须显示样本量；
- 低样本量降低置信度；
- 区分单一竞品问题和跨竞品问题；
- 区分旧评论和近期评论；
- 区分消费者期望与商品事实；
- 允许用户查看支持和反对证据；
- 原始评论模式与聚合主题模式分开标记。

---

## 10. 商品机会评分

### 10.1 总体原则

机会评分用于排序和提示，不代表销量或利润预测。系统同时显示：

- 分项得分；
- 总分；
- 置信度；
- 缺失维度；
- 数据截至时间；
- 计算版本。

### 10.2 商品机会分

```text
商品机会分 =
需求强度 × 20%
+ 增长与时效性 × 15%
+ 竞争缺口 × 15%
+ 评论痛点机会 × 20%
+ 差异化空间 × 10%
+ 单位经济性 × 10%
+ 风险可控性 × 10%
```

各项归一化为 0～100。

| 维度 | 示例依据 |
|---|---|
| 需求强度 | 搜索兴趣、排名、评论增长、候选池表现 |
| 增长与时效性 | 近期趋势、季节性、数据新鲜度 |
| 竞争缺口 | 竞品集中度、同质化、低评分主题 |
| 评论痛点机会 | 痛点频率、严重度和评分影响 |
| 差异化空间 | 竞品未覆盖且可以验证的改进方向 |
| 单位经济性 | 售价、成本、物流、平台费用和广告成本 |
| 风险可控性 | 合规、知识产权、供应链和退货风险 |

### 10.3 痛点机会分

```text
痛点机会分 =
出现频率 × 25%
+ 严重程度 × 20%
+ 对星级的影响 × 20%
+ 跨竞品普遍性 × 15%
+ 时间新鲜度 × 10%
+ 解决可行性 × 10%
```

### 10.4 Listing 卖点分

```text
卖点质量分 =
商品事实支持度 × 30%
+ 评论需求支持度 × 25%
+ 差异化程度 × 15%
+ 表达清晰度 × 10%
+ 关键词相关性 × 10%
+ 合规风险控制 × 10%
```

### 10.5 缺失数据处理

系统不应把缺失维度直接视为 0，也不应由模型猜测。输出示例：

```json
{
  "score": 76,
  "confidence": 0.61,
  "missing_dimensions": [
    "supplier_cost",
    "advertising_cost",
    "absolute_search_volume"
  ],
  "warning": "当前结果主要反映评论痛点和竞品信息，不构成完整利润判断"
}
```

### 10.6 评分版本化

所有评分记录：

```text
score_version
weights
normalization_method
input_snapshot_id
computed_at
```

---

## 11. 商品事实与 Agent 边界

### 11.1 三类信息

系统必须区分：

| 类型 | 含义 | 能否直接写入 Listing |
|---|---|---:|
| Fact | 经用户或文档确认的商品事实 | 可以 |
| Inference | 根据数据形成的推断 | 需谨慎表达 |
| Suggestion | 产品改进或营销建议 | 不可以当作现有能力 |

### 11.2 商品事实状态

```text
unverified
user_confirmed
document_confirmed
rejected
expired
```

### 11.3 不可变硬边界

- 未确认属性不能写成现有功能；
- 不得将消费者期望描述成商品事实；
- 不得将竞品功能移植到当前商品；
- 不得自动生成未提供的检测、认证和性能结论；
- 不得在图片中增加不存在的配件和结构；
- 外部发布必须明确授权；
- 生成、编辑、确认和导出行为保留审计记录。

### 11.4 可迭代边界

以下内容可随着产品使用逐步调整：

- 自动接受低风险洞察；
- 批量任务数量；
- 评分权重；
- 自动重试策略；
- 生成版本数量；
- 聊天可以发起的工作流操作；
- 不同类目的风险阈值。

---

## 12. Listing 生成系统

### 12.1 第一版输出

- 英文商品标题；
- 五点描述；
- 产品描述；
- 搜索关键词；
- 中文对照；
- 图片 Creative Brief；
- 事实检查报告；
- 平台规则检查报告；
- Markdown、JSON、CSV 导出。

### 12.2 生成输入

```text
目标平台规则
+ 商品事实
+ 已接受洞察
+ 目标人群
+ 使用场景
+ 关键词
+ 风险限制
+ 品牌语气
```

### 12.3 生成约束

- 只允许引用已确认商品事实；
- 对每条卖点记录依据；
- 未知属性使用缺失提示，不进行补全；
- 提示词和模型版本可追踪；
- 用户可以针对单一字段重新生成；
- 重新生成不得覆盖已批准版本；
- 所有版本可比较和回滚。

### 12.4 检查项目

- 事实一致性；
- 未确认声明；
- 标题和字段长度；
- 关键词堆砌；
- 绝对化与误导性表达；
- 材质、尺寸、容量和配件冲突；
- 语言和地区表达；
- 类目特定规则；
- 内容完整性。

---

## 13. GPT Image 2 视觉生成系统

### 13.1 模型定位

GPT Image 2 的官方模型 ID 为 `gpt-image-2`，支持文本与图像输入，可用于图片生成和编辑，并支持 Image API 与 Responses API。

参考：[OpenAI GPT Image 2 官方文档](https://developers.openai.com/api/docs/models/gpt-image-2)

图像模型通过可替换的 `ImageModelProvider` 接入，不与业务逻辑绑定。

### 13.2 图片类型

```text
main_image_edit
lifestyle_image
feature_image
comparison_image
size_image
detail_page_section
```

### 13.3 主图边界

Amazon 主图要求准确呈现实际商品，通常要求纯白背景、无额外文字或图形，并且商品占据主要画面。主图应基于真实商品照片处理，不从一句描述凭空生成商品。

参考：[Amazon Product Image Requirements](https://sellercentral.amazon.com/seller-forums/discussions/t/7366420bc9ccfb8656594e6edcf4ece6)

主图允许：

- 去除或清理背景；
- 校正光线；
- 修正构图；
- 去除非结构性灰尘；
- 保持商品外观、颜色、数量和配件不变。

主图禁止：

- 生成不存在的结构；
- 增加未包含配件；
- 改变颜色或变体；
- 添加促销文案、Logo、水印或图标；
- 使用与真实商品不一致的纯合成图。

### 13.4 详情图流程

```text
真实商品图
+ 商品事实
+ 评论洞察
+ 目标用户
+ 视觉风格
+ Amazon规则
        ↓
Creative Brief
        ↓
GPT Image 2 生成或编辑视觉底图
        ↓
商品一致性检查
        ↓
程序添加标题、尺寸、图标和品牌元素
        ↓
平台规则检查
        ↓
人工审核
```

### 13.5 文字排版

图像模型负责视觉底图，文字、尺寸和品牌元素由确定性排版系统生成。原因包括：

- 保证拼写正确；
- 保证尺寸数字准确；
- 保证中英文切换一致；
- 统一字体和品牌规范；
- 同一底图可以复用到多个语言版本；
- 避免模型在图片中生成乱码或错误文字。

### 13.6 输入图片最低标准

硬性要求：

- 必须是真实待售商品；
- 最长边至少 1000 像素，建议 1600 像素以上；
- JPG 或 PNG；
- 商品主体清晰；
- 颜色、配件和变体与目标 Listing 一致；
- 提供 SKU 或变体标识；
- 提供包装包含物清单；
- 用户确认拥有图片使用权。

推荐上传：

1. 正面或 45 度视角；
2. 背面；
3. 左右侧面；
4. 结构和材质特写；
5. 全部配件平铺；
6. 尺寸参考图。

### 13.7 图片检查

- 商品外观一致性；
- 数量和配件一致性；
- 颜色和变体一致性；
- 场景比例合理性；
- 文案和数字正确性；
- 主图背景和占比；
- 禁止元素；
- 图片清晰度；
- 用户最终确认。

### 13.8 “高转化”的产品表述

第一阶段使用：

> 生成以转化为目标、符合商品事实与平台规则的商品视觉素材。

不直接声称“保证高转化”。真实转化提升需要上线后的 A/B 测试、点击率和订单数据支持。

---

## 14. 国际化设计

### 14.1 界面国际化

- 所有界面文字使用资源键；
- 中文和英文资源分离；
- 不在组件中硬编码界面文案；
- 日期、数字、币种和时区按 Locale 格式化；
- 错误消息支持中英文；
- 用户可以独立选择界面语言和 Listing 语言。

### 14.2 内容国际化

以下内容分别保存不同 Locale 版本：

- Listing；
- 图片文字；
- 风险说明；
- 导出模板；
- 商品机会卡摘要。

### 14.3 字段设计

不使用：

```text
title_cn
title_en
```

建议使用：

```json
{
  "translations": {
    "zh-CN": {"title": "..."},
    "en-US": {"title": "..."}
  }
}
```

---

## 15. 技术架构

### 15.1 总体选择

采用模块化单体与异步任务工作流，不在第一阶段拆分微服务。

### 15.2 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | Next.js、React、TypeScript |
| UI | Tailwind CSS 与可访问组件库 |
| 国际化 | next-intl 或同类方案 |
| 后端 | FastAPI、Pydantic |
| ORM与迁移 | SQLAlchemy、Alembic |
| 数据库 | PostgreSQL |
| 向量检索 | pgvector |
| 缓存与队列 | Redis |
| 后台任务 | Redis 队列与独立 Worker |
| 文件存储 | MinIO 或 S3 兼容存储 |
| AI模型 | 可替换文本、嵌入与图像 Provider |
| 接口 | REST、OpenAPI |
| 部署 | Docker Compose |
| CI | GitHub Actions |
| 可观测性 | 结构化日志、错误追踪、成本和延迟指标 |

### 15.3 后端模块

```text
app/
  identity/       用户、工作空间与权限
  projects/       分析项目
  catalog/        商品、SKU与变体
  ingestion/      CSV、JSON、XLSX与API导入
  sources/        数据来源、许可和新鲜度
  reviews/        评论清洗与分析
  competitors/    竞品比较
  opportunities/ 商品机会卡与评分
  facts/          商品事实与确认
  listings/       Listing生成和版本管理
  creatives/      图片与详情页视觉素材
  compliance/     事实、图片和平台规则检查
  workflows/      工作流状态与人工确认
  chat/           辅助聊天
  providers/      模型、数据源和存储适配器
  evals/          Agent回归评测
  audit/          审计日志
  localization/   国际化内容
```

### 15.4 模型 Provider

```text
InsightModelProvider
ListingModelProvider
EmbeddingProvider
ImageModelProvider
ModerationProvider
```

Provider 接口负责：

- 统一调用协议；
- 重试与超时；
- 模型选择；
- 用量和费用记录；
- 输入输出审计；
- 错误分类；
- 测试 Mock。

### 15.5 成熟产品要求

- 后台任务可恢复；
- 幂等任务设计；
- 数据库迁移可回滚；
- API 版本化；
- Schema 版本化；
- 失败任务可重试；
- 限流和并发控制；
- 文件病毒与类型检查；
- 数据导出与删除；
- 日志脱敏；
- 密钥不进入日志；
- 评测随版本自动运行。

---

## 16. 核心数据模型

### 16.1 通用字段

所有核心对象至少包含：

```text
id
schema_version
created_at
updated_at
created_by
```

### 16.2 Project

```text
id
workspace_id
name
marketplace
target_locale
interface_locale
currency
status
created_at
updated_at
```

### 16.3 ProductCandidate

```text
id
project_id
external_id
category
title
brand
price
currency
rating
review_count
source_id
observed_at
```

### 16.4 ProductVariant

```text
id
product_id
sku
external_id
color
size
package_quantity
status
```

### 16.5 Review

```text
id
product_id
external_review_id
rating
title
body
language
reviewed_at
verified_purchase
source_id
content_hash
```

### 16.6 ProductFact

```text
id
product_id
variant_id
fact_type
value
unit
source
verification_status
verified_by
verified_at
expires_at
```

### 16.7 Insight

```text
id
product_id
topic
summary
sentiment
frequency
severity
rating_impact
recency_score
cross_competitor_score
confidence
status
```

### 16.8 Evidence

```text
id
insight_id
evidence_type
source_entity_id
excerpt
support_strength
observed_at
```

### 16.9 OpportunityCard

```text
id
product_id
schema_version
target_audience
use_cases
competitor_gaps
differentiation_ideas
keywords
opportunity_score
score_version
confidence
missing_dimensions
risk_flags
status
```

### 16.10 ListingVersion

```text
id
product_id
marketplace
locale
title
bullet_points
description
search_terms
model
prompt_version
input_snapshot_id
status
created_at
```

### 16.11 CreativeAsset

```text
id
product_id
variant_id
asset_type
locale
source_images
creative_brief
prompt
model
output_path
consistency_status
compliance_status
human_review_status
created_at
```

### 16.12 SourceRecord

```text
id
source_type
source_name
source_url
license
usage_scope
observed_at
imported_at
expires_at
user_attested
raw_payload_hash
```

### 16.13 WorkflowRun

```text
id
project_id
workflow_type
current_step
status
input_snapshot
output_snapshot
estimated_cost
actual_cost
started_at
finished_at
```

### 16.14 AuditEvent

```text
id
workspace_id
actor
action
entity_type
entity_id
before
after
created_at
```

---

## 17. Schema 版本化

“冻结字段”表示为某个发布版本确定稳定的数据契约，而不是永远禁止修改。

例如：

```text
OpportunityCard v1
OpportunityCard v2
```

版本升级要求：

- Schema 携带版本号；
- 提供数据库迁移；
- 旧数据能够读取或升级；
- 删除字段前先标记弃用；
- API 返回版本明确；
- 评测数据标注 Schema 版本；
- 前端兼容仍受支持的版本。

---

## 18. API Key、费用与安全

### 18.1 费用策略

自托管版本采用 BYOK：

```text
Bring Your Own Key
用户使用自己的模型API Key
费用计入用户自己的模型账户
```

### 18.2 密钥要求

- API Key 只由后端读取；
- 不放入浏览器或移动端；
- 不提交到 GitHub；
- 默认使用环境变量；
- 日志自动遮盖；
- 支持密钥轮换；
- 可选外部密钥管理系统；
- 提供 `.env.example`；
- CI 执行敏感信息扫描。

OpenAI 官方建议 API Key 不应部署在客户端或提交到代码仓库，请求应通过后端处理：

- [OpenAI API Key Safety](https://help.openai.com/en/articles/5112595-best-practices-for-api-key)

### 18.3 成本控制

- 任务开始前估算费用；
- 用户设置单任务预算；
- 限制图片变体数量；
- 超出预算前确认；
- 记录文本、图像和嵌入费用；
- 缓存可复用结果；
- 支持低成本与高质量模型档位；
- 失败重试有上限。

### 18.4 上传数据安全

- 限制文件大小和类型；
- 防止公式注入；
- 隔离对象存储路径；
- 导入前预览；
- 日志不记录完整敏感内容；
- 支持项目数据删除；
- 导出包含来源与风险说明。

---

## 19. 自托管与未来托管

### 19.1 第一阶段

自托管优先：

- Docker Compose 一键启动；
- 用户自行配置数据库、存储与 API Key；
- 数据保留在用户环境；
- 项目不承担用户模型调用费用。

### 19.2 托管就绪

架构预留：

- Workspace 隔离；
- 多用户身份；
- 权限控制；
- 存储隔离；
- 用量统计；
- 配额与限流；
- 审计；
- 数据导出和删除。

### 19.3 未来官方托管版

如果未来提供在线托管服务，需要额外建设：

- 用户认证；
- 多租户安全；
- 支付和配额；
- 数据处理协议；
- 隐私政策；
- 备份和灾难恢复；
- 滥用检测；
- 服务可用性监控；
- 模型费用结算。

托管版不建议长期保存用户个人模型 Key，更适合由服务端统一调用并按套餐或用量结算。

---

## 20. 轻量测评方案

### 20.1 核心研究假设

> 与普通大模型直接生成相比，基于评论证据和商品事实约束的 Agent，能够减少无依据卖点和事实错误，并生成更具实际使用价值的 Listing。

### 20.2 测试商品

- 压缩旅行收纳袋；
- 玻璃喷油壶；
- 车载垃圾桶。

### 20.3 对比版本

每个商品生成：

- 普通大模型直接生成版；
- Insight2Listing Agent 版。

总计 6 份匿名结果。

### 20.4 自动测试

- 输出完整性；
- Schema 正确性；
- 引用记录是否存在；
- 商品事实一致性；
- 字段长度；
- 禁止表达；
- 重复运行稳定性；
- 缺失数据处理；
- 工作流失败恢复。

### 20.5 项目组核验

- 每个商品前 5 项主要洞察；
- 每项抽查 3 条证据；
- 核验全部 Listing 商品事实；
- 检查所有图片中的商品结构、颜色、数量和配件；
- 记录严重、一般和轻微错误。

### 20.6 行业快速盲评

邀请 1～2 名行业人员：

- 不要求操作系统；
- 匿名查看 3 组结果；
- 每组进行两两选择；
- 每人控制在 15～20 分钟。

问题：

1. 哪个版本更准确地抓住消费者需求？
2. 哪个版本的卖点更适合作为 Listing 初稿？
3. 哪个版本存在更多夸大或不可靠信息？
4. 如果继续修改，愿意选择哪个版本？
5. 最有价值与最需要改进的地方是什么？

### 20.7 主要指标

| 指标 | 第一阶段目标 |
|---|---:|
| 完整任务完成率 | ≥ 95% |
| 引用记录存在率 | 100% |
| 商品事实一致率 | 100% |
| 未确认功能写入次数 | 0 |
| 核心卖点可追溯率 | 100% |
| 主要痛点覆盖率 | 不低于普通大模型 |
| 行业评审偏好 | 多数选择 Agent 版 |

### 20.8 图片指标

- 商品外观一致率；
- 配件准确率；
- 文字正确率；
- 图片规则通过率；
- 人工修改率；
- 最终采用率；
- 视觉盲评偏好。

### 20.9 一票否决

- 编造评论或数据来源；
- 把未确认需求写成商品已有能力；
- 图片增加不存在的结构或配件；
- 生成可能直接导致错误上架的严重事实；
- 泄露 API Key 或用户数据。

### 20.10 后续测评

以下内容不属于第一阶段结论：

- 大规模用户效率实验；
- 真实店铺点击率和转化率 A/B 测试；
- 销量提升；
- 长周期价格策略；
- 全品类适用性。

---

## 21. GitHub 仓库规划

```text
insight2listing/
  apps/
    web/
    api/
    worker/
  packages/
    schemas/
    ui/
    i18n/
    rules/
    prompts/
    evals/
  infrastructure/
    docker/
    migrations/
  examples/
    synthetic-data/
  docs/
    zh-CN/
    en-US/
  tests/
  .github/
    workflows/
  LICENSE
  README.md
  README.zh-CN.md
  CONTRIBUTING.md
  SECURITY.md
  PRIVACY.md
  DATA_LICENSE.md
  THIRD_PARTY_NOTICES.md
  DISCLAIMER.md
  .env.example
  docker-compose.yml
```

### 21.1 MIT 范围

MIT License 只覆盖项目源代码。以下内容需要独立许可：

- 测试数据；
- Amazon 数据；
- 商品图片；
- 品牌 Logo；
- 字体；
- 图标；
- 用户上传内容；
- 第三方模型输出的具体使用限制。

### 21.2 README 必须包含

- 产品定位；
- 功能截图；
- 中英文快速开始；
- Docker 安装；
- API Key 配置；
- 数据来源声明；
- 示例数据说明；
- 安全警告；
- 当前能力边界；
- 测评运行方法；
- 路线图。

---

## 22. 分阶段实施路线

项目没有固定截止日期，但仍应以能力门槛划分阶段，避免无限扩张。

### 阶段 A：工程基础

- 建立 Monorepo；
- 中英文界面框架；
- FastAPI 和 PostgreSQL；
- 用户、工作空间和项目；
- Docker Compose；
- CI、测试和数据库迁移；
- Provider 接口；
- 审计与任务状态。

完成标准：

- 新环境可按文档启动；
- 中英文界面可切换；
- 数据库迁移和测试自动运行；
- API Key 不进入客户端和日志。

### 阶段 B：数据导入与规范化

- CSV、JSON、XLSX；
- 字段映射；
- 数据预览；
- 数据校验；
- 来源与许可记录；
- 去重和导入报告；
- 合成演示数据。

完成标准：

- 三种测试商品均能从三种格式导入；
- 错误行可以定位；
- 重复导入不产生重复记录；
- 数据截至时间可见。

### 阶段 C：评论洞察与机会卡

- 评论清洗；
- 语言识别；
- 主题和情感分析；
- 证据绑定；
- 跨竞品比较；
- 机会评分；
- 人工接受和拒绝。

完成标准：

- 每项核心洞察有证据；
- 分数、置信度和缺失维度可解释；
- 结果可以保存并版本化。

### 阶段 D：Listing 工作台

- 商品事实中心；
- 标题、五点和描述生成；
- 搜索词；
- 中英文对照；
- 版本管理；
- 事实和规则检查；
- 导出包。

完成标准：

- 未确认事实不能进入最终批准版本；
- 三个测试商品完成完整工作流；
- 自动检查全部通过。

### 阶段 E：视觉生成

- 商品图上传和检查；
- Creative Brief；
- GPT Image 2 Provider；
- 主图编辑；
- 详情图生成；
- 确定性文字排版；
- 图片一致性和规则检查；
- 图片版本管理。

完成标准：

- 主图基于真实商品图；
- 不出现不存在配件；
- 中英文图片文字准确；
- 图片在人工批准后才能导出。

### 阶段 F：评测和开源发布

- 固定评测集；
- 普通大模型基线；
- 自动回归评测；
- 项目组证据核验；
- 行业快速盲评；
- 双语文档；
- MIT 与数据许可说明；
- 首个稳定版本发布。

### 阶段 G：实时数据和卖家 Beta

- Amazon SP-API 连接器；
- 沙箱和 Mock 测试；
- 找到愿意参与的真实卖家；
- OAuth 有限授权；
- 生产数据验证；
- 数据刷新和撤销授权；
- 评估自动上架能力。

---

## 23. 风险登记

| 风险 | 影响 | 应对 |
|---|---|---|
| 无法获得最新完整评论 | 评论分析数据不足 | 用户导入、官方聚合主题、第三方连接器 |
| 数据许可不明确 | 法律和平台风险 | 不内置爬虫，记录来源和许可，仓库使用合成数据 |
| AI 编造商品事实 | 错误 Listing | Fact/Inference/Suggestion 隔离和硬校验 |
| 图片改变商品结构 | 误导消费者 | 真实图片输入、一致性检查和人工审核 |
| 平台规则变化 | 导出内容过时 | 规则版本化并显示更新时间 |
| 用户API Key泄露 | 费用和安全风险 | 后端保管、日志脱敏、环境变量和密钥扫描 |
| 模型成本失控 | 用户费用过高 | 预算、缓存、变体限制和费用预估 |
| 项目范围过大 | 长期无法发布 | 以阶段完成标准控制扩张 |
| 模型更新导致回归 | 输出质量下降 | 固定评测集、版本锁定和自动回归测试 |
| 中英文内容不一致 | 用户误解 | Locale 分离、对照检查和确定性排版 |

---

## 24. 已确定与后续事项

### 24.1 已确定

- 产品名：Insight2Listing；
- Amazon 美国站首发；
- 工作流系统为主，聊天为辅；
- 中英文双界面；
- MIT 开源；
- 自托管优先、托管就绪；
- 用户承担模型费用；
- CSV、JSON、XLSX 与 API 适配架构；
- PostgreSQL、Redis 和对象存储；
- 模块化单体与异步任务；
- Schema 版本化；
- 商品事实需要人工确认；
- GPT Image 2 接入；
- 主图基于真实商品照片；
- 详情图可以使用 AI 生成；
- 图片文字由程序确定性排版；
- 三个测试商品；
- 轻量测评方案；
- 卖家授权和生产 SP-API 接入放到后续。

### 24.2 后续按阶段决定

- 首批可再分发真实数据集；
- 第三方数据提供商；
- 具体文本和嵌入模型；
- 正式 UI 视觉风格；
- 各类目详细规则；
- 官方托管版商业模式；
- Amazon 自动上架；
- 其他站点和平台；
- 大规模用户实验；
- 真实转化率 A/B 测试。

---

## 25. 最终定义

Insight2Listing 的第一阶段不是一个自动抓取 Amazon、预测爆款并直接上架的黑盒工具，而是一套面向 Amazon 美国站的成熟、可扩展、可审计工作流：

> 用户提供有权使用的数据和真实商品资料，Agent 从评论与竞品信息中形成可追溯的市场洞察，帮助用户验证候选商品，并将经过确认的商品事实转化为 Listing 与视觉素材；系统对事实、图片和平台规则进行检查，由用户完成最终审核与导出。

它的核心差异不在于“能生成文案和图片”，而在于：

1. 洞察有来源；
2. 建议与事实分离；
3. Listing 有约束；
4. 图片基于真实商品；
5. 不确定性可见；
6. 工作流可复现；
7. 模型、数据和规则都可以替换与版本化。

这套定义既保留长期成为跨境电商智能上新平台的空间，也为个人开源项目提供可执行、可验证的工程边界。
