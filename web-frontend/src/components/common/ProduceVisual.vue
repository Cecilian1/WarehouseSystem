<script setup lang="ts">
import { computed } from 'vue'
import { Leaf } from 'lucide-vue-next'
import { resolveProduceImage } from '@/utils/produceImage'

const props = withDefaults(defineProps<{
  name: string
  color?: string
  size?: 'small' | 'medium' | 'large'
  src?: string
}>(), {
  color: '#4f8cff',
  size: 'medium',
  src: '',
})

const imageSrc = computed(() => resolveProduceImage(props.name, props.src))
</script>

<template>
  <div
    class="produce-visual"
    :class="[`is-${size}`, { 'has-image': Boolean(imageSrc) }]"
    :style="{ '--produce-color': color }"
  >
    <img v-if="imageSrc" class="produce-visual__photo" :src="imageSrc" :alt="name">
    <template v-else>
      <div class="produce-visual__mesh" />
      <div class="produce-visual__fruit"><Leaf :size="size === 'large' ? 28 : 17" /></div>
      <span>{{ name.slice(0, 1) }}</span>
    </template>
  </div>
</template>

<style scoped>
.produce-visual {
  --visual-size: 48px;
  position: relative;
  display: grid;
  width: var(--visual-size);
  height: var(--visual-size);
  flex: 0 0 auto;
  place-items: center;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--produce-color) 36%, transparent);
  border-radius: 12px;
  color: white;
  background:
    radial-gradient(circle at 35% 25%, color-mix(in srgb, var(--produce-color) 84%, white), transparent 30%),
    linear-gradient(145deg, color-mix(in srgb, var(--produce-color) 75%, #203046), color-mix(in srgb, var(--produce-color) 35%, #0c1828));
  box-shadow: inset 0 0 30px rgba(255, 255, 255, .08);
}
.produce-visual.is-small { --visual-size: 38px; border-radius: 10px; }
.produce-visual.is-large { --visual-size: 220px; border-radius: 18px; }
.produce-visual.has-image {
  border-color: rgba(255, 255, 255, .08);
  background: #f4f1ea;
}
.produce-visual__photo {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.produce-visual__mesh { position: absolute; inset: 0; opacity: .23; background-image: linear-gradient(rgba(255,255,255,.18) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.18) 1px, transparent 1px); background-size: 15px 15px; transform: perspective(90px) rotateX(55deg) scale(1.8); }
.produce-visual__fruit { position: absolute; top: 12%; right: 12%; opacity: .38; }
.produce-visual span { position: relative; font-size: calc(var(--visual-size) * .3); font-weight: 760; text-shadow: 0 3px 12px rgba(0,0,0,.28); }
</style>
