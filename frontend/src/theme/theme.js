export const wtTheme = {
  dark: true,
  colors: {
    background: '#14161B',
    surface: '#1B1E25',
    'surface-variant': '#242833',
    'surface-2': '#242833',
    primary: '#5EEAD4',
    secondary: '#F5A623',
    accent: '#5EEAD4',
    success: '#5EEAD4',
    warning: '#F5A623',
    error: '#E8607B',
    info: '#7FB2E5',
    border: '#2A2E38',
    'on-background': '#E7E9EE',
    'on-surface': '#E7E9EE',
  },
}

export const wtVuetify = {
  theme: {
    defaultTheme: 'wt',
    themes: { wt: wtTheme },
  },
  defaults: {
    VBtn: { rounded: '0', variant: 'outlined' },
    VBtnToggle: { rounded: '0', variant: 'outlined', divided: true },
    VCard: { rounded: '0', elevation: 0 },
    VSheet: { rounded: '0' },
    VChip: { rounded: '0' },
    VAlert: { rounded: '0' },
    VSnackbar: { rounded: '0' },
    VTextField: { variant: 'outlined', density: 'comfortable', hideDetails: 'auto' },
    VSelect: { variant: 'outlined', density: 'comfortable', hideDetails: 'auto', rounded: '0' },
    VRangeSlider: { hideDetails: 'auto' },
  },
}
