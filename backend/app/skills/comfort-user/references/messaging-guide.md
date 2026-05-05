# Support Messaging Guide

## Tone Per Trigger

### Low Match Score
**Tone**: Objective + Solution-oriented

> "匹配度虽然不高，但这说明不了你的能力。差距主要在 [X]，通过 [Y] 可以提升。这里有一位情况相似的求职者..."

### Application Rejected
**Tone**: Empathetic + Forward-looking

> "被拒确实不好受。每次拒绝都是一次校准——你离那个适合你的位置更近了。有位求职者投了 80 份简历后才拿到 Offer..."

### Interview Failed
**Tone**: Supportive + Growth-focused

> "面试是双向选择。这次的经验会让你下次准备更充分。来听听这位的经历..."

### Offer Received
**Tone**: Celebratory + Humble

> "太棒了！你的努力得到了回报。每一位拿到 Offer 的求职者背后都有故事..."

### New User Onboarding
**Tone**: Warm + Welcoming

> "欢迎！求职路上我们一起走。这里是你当前的技能画像..."

## Structure Template

```
1. Acknowledge (1 sentence) — validate their feeling
2. Share (2-3 sentences) — a similar story from RAG
3. Encourage (1 sentence) — forward-looking close
```

## Rules
- Never exceed 200 characters total
- Always grounded in a specific retrieved story (not generic platitudes)
- Never use toxic positivity ("just be positive!")
- If no matching story found in Chroma → use a general encouragement template
