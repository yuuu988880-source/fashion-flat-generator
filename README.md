# Fashion Flat Generator

将模特上身图转成保留可见款式特征的服装单体手绘线稿，再基于同一母版上色。开源 Agent Skill，附本地任务准备工具。

**实际图像生成由支持参考图片编辑的宿主完成。Python 脚本仅准备任务，不包含模型，不会假装识别图片或输出固定款式。**

## 直接调用

安装到 Codex 的个人 skills 目录后，在新对话中附上服装原图并输入：

```text
使用 $fashion-flat-generator
把上传的模特上身图转为服装单体手绘线稿，再基于同一母版同步上色。
保留可见版型、比例、领型、袖型、纽扣和褶裥；未知结构标注，不新增设计。
交付黑白线稿、配对上色图和简短核对说明。
```

如果上传整套 look，说明目标单品，例如“只画外套”。风格参考与商品原图分别标注。输入只有正面时不会伪造背面；需要背面还原时补充背面照片。

## 安装

新安装（目标目录须不存在）：

```bash
git clone https://github.com/yuuu988880-source/fashion-flat-generator.git ~/.codex/skills/fashion-flat-generator
```

已有该技能时先保留本地改动，再更新仓库。`SKILL.md` 也可供其他支持技能指令及图像编辑的宿主读取。需要生成时，宿主必须具备真正的参考图编辑能力；文本模型单独运行只会得到任务与提示词。

Lovable 工作区可使用 `integrations/lovable/skill-template.md`，这是自包含指令，无本地相对文件依赖；创建 Lovable 工作区技能时，将其全文作为 SKILL.md 内容提交。仓库中使用模板文件名，避免 Codex 把它重复识别为同名技能。工作区技能不会自动创建应用、安装图像 API 或读取你的电脑文件。若要求生成应用，按技能中上传→结构观察→线稿→上色→对照的流程实现真实服务连接。

## 工作流

1. 看图并记录目标服装、可见结构、相对比例、颜色和未知部分。
2. 生成白底手绘线稿，检查与原图的领肩袖、轮廓和装饰是否相符。
3. 编辑已经检查的同一张线稿上色，原照片只提供色彩和表面观感。
4. 对照两图核验结构是否漂移，修复后交付；剩余偏差标为草稿。

轮廓更重、内部结构线更细，保留有意义的褶裥线；不迁移风格参考的设计、签名或商标。不从外观断言纤维成分。输出是视觉款式图，不能代替测量、纸样或制造工艺验证。图像模型不能保证像素级一致；真正需要严格锁定应保留原墨线图层，只改下方色层。

## 可选命令行准备

Python 3.9+，无第三方依赖。先由人或视觉宿主查看原图，将 `examples/observation.example.json` 改成该款的真实观察，并设 `example_only` 为 `false`。

```bash
python3 fashion_flats_full_pipeline.py \
  --image /path/model-front.png \
  --observations /path/observations.json \
  --out output/job-line
```

可重复 `--image` 提供同款角度；`--style-reference` 只提供绘画风格。创建的任务包含已复制输入、观察、prompt 和 SHA-256 清单。没有母版时上色状态为 `blocked_missing_line_master`。

宿主生成并检查线稿后准备上色任务：

```bash
python3 fashion_flats_full_pipeline.py \
  --image /path/model-front.png \
  --observations /path/observations.json \
  --line-master /path/front_line.png \
  --out output/job-color
```

再由宿主真实执行图片编辑。脚本不会调用外部 API、分析图片、测量服装或生成 SVG。输入签名检查不等于完整图像解码，宿主必须实际打开图片。已有输出目录不会覆盖。

## 验证

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖输入缺失/伪装图片、观察结构、禁止使用示例、不同服装对应不同 prompt、母版依赖、素材哈希和不覆盖输出。自动测试验证任务准备逻辑，不证明所有服装的绘图精度。视觉质量必须逐款检查。

## 从 Gemini 草稿修正了什么

- 原 `SKILL.md` 实际是 RTF，现为可读取的 UTF-8 Markdown。
- 原“分析”忽略输入、总是输出同一件蝴蝶结裙；已移除固定 anatomy 和 SVG 模板。
- 删除无证据的材质、YKK 拉链、背面省道及“工业制造标准”承诺。
- 上色必须依赖线稿母版，区分任务准备、实际执行和质量核对状态。
- 移除未使用的 SDK 依赖，不需要把密钥写进技能。

## 隐私与许可证

MIT，见 [LICENSE](LICENSE)，保留原草稿版权声明。许可证仅覆盖仓库代码与文字；不授予第三方品牌、照片和参考作品权利。照片、参考截图、生成图、任务目录和本地备份未包含在本仓库。公开分享示例前应确认素材使用权。
