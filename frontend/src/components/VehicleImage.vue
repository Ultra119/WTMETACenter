<template>
  <div class="veh-img-wrap" :style="wrapStyle">

    <Transition name="fade">
      <img
        v-if="src && loaded"
        :src="src"
        :alt="name"
        class="veh-img"
        draggable="false"
      />
    </Transition>

    <Transition name="fade">
      <div v-if="src && !loaded && !imgError && showFallback" class="veh-img-skeleton" />
    </Transition>

    <Transition name="fade">
      <div v-if="(imgError || !src) && showFallback" class="veh-img-placeholder">
        <v-icon :size="iconSize" style="opacity:.14;color:var(--primary)">mdi-image-outline</v-icon>
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { computed, toRef, watch } from 'vue'
import { useVehicleImage } from '../composables/useVehicleImage.js'

const props = defineProps({
  name:         { type: String,  default: null  },
  identifier:   { type: String,  default: null  },
  type:         { type: String,  default: null  },
  aspect:       { type: String,  default: '2/1' },
  fit:          { type: String,  default: 'cover' },
  showFallback: { type: Boolean, default: true   },
})

const emit = defineEmits(['loaded', 'error'])

const identifierRef = toRef(props, 'identifier')
const typeRef       = toRef(props, 'type')
const { src, loaded, error: imgError } = useVehicleImage(identifierRef, typeRef)

watch(loaded,   v => { if (v) emit('loaded') })
watch(imgError, v => { if (v) emit('error')  })

const wrapStyle = computed(() => ({
  aspectRatio: props.aspect,
  '--veh-fit':  props.fit,
}))

const iconSize = computed(() => props.aspect === '1/1' ? 28 : 36)
</script>

<style scoped>
.veh-img-wrap        { position: relative; width: 100%; overflow: hidden; background: rgba(231, 233, 238, 0.04); }
.veh-img,
.veh-img-skeleton,
.veh-img-placeholder { position: absolute; inset: 0; }
.veh-img             { width: 100%; height: 100%; display: block; object-fit: var(--veh-fit, cover); object-position: center; }
.veh-img-placeholder { display: flex; align-items: center; justify-content: center; }
.veh-img-skeleton {
  background: linear-gradient(90deg, transparent 0%, rgba(231, 233, 238, 0.07) 50%, transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 1.6s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
</style>
