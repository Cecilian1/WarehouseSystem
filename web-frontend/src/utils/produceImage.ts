import apple from '@/assets/produce/apple.jpg'
import banana from '@/assets/produce/banana.jpg'
import carrot from '@/assets/produce/carrot.jpg'
import cucumber from '@/assets/produce/cucumber.jpg'
import orange from '@/assets/produce/orange.jpg'

// 图片来自 Wikimedia Commons，公有领域 / CC0：
// Apple、Banana、Orange：NCI / Renee Comet
// Carrot：Titus Tscharntke
// Cucumber：WiseMan42
const PRODUCE_IMAGES: Array<{ keys: string[]; src: string }> = [
  { keys: ['苹果', 'apple'], src: apple },
  { keys: ['香蕉', 'banana'], src: banana },
  { keys: ['胡萝卜', 'carrot'], src: carrot },
  { keys: ['黄瓜', 'cucumber'], src: cucumber },
  { keys: ['橙子', '香橙', 'orange'], src: orange },
]

export function resolveProduceImage(name: string, src?: string) {
  const custom = src?.trim()
  if (custom && !custom.startsWith('#')) return custom

  const normalized = name.trim().toLowerCase()
  const matched = PRODUCE_IMAGES.find((item) =>
    item.keys.some((key) => normalized.includes(key.toLowerCase())),
  )
  return matched?.src || ''
}
