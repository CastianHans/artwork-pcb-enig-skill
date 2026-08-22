# Image repair and separation prompts

Use image generation only when the source needs semantic repair. Inspect the result against the source before running manufacturing scripts.

## Clean master prompt

> 使用我上传的原图作为唯一构图与内容参考，生成高清、干净、平滑的矢量插画感修复版。严格保持人物姿势、比例、服装、装饰、边框和全部抽象符号的位置与形状；不新增、不删除、不把符号识别成字母或文字。清除压缩噪点和像素毛刺，补齐明显断裂的轮廓，把色块恢复为均匀纯色。保持原画布比例和安全边距。大部分线宽一致，只在原图明确表现压感、遮挡或关节转折的位置轻微加粗。

## Registered line-art prompt

> 以上一张已经确认的修复母版为唯一参考，不重新设计构图。只提取用户指定的描边、边框、装饰线、星芒和抽象符号，生成纯黑线条、纯白背景的高清矢量线稿感图。删除颜色、阴影、渐变和纹理；补齐断线，消除噪点、锯齿、重复边和孤立碎片。严格保留抽象符号的形状，不把它们变成字母。画布、比例、原点和内容位置必须与修复母版完全一致。

## Review gate

- Compare at least four separated anchors: top decoration, face/chin, central ornament, and footer symbols.
- Reject identity, costume, symbol, pose, crop, or canvas changes.
- Prefer one approved result over combining independently generated fragments.
- To reduce Codex image-generation usage, the user may generate on the web and return the original plus one or two best candidates.
