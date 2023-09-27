import { StoryObj } from '@storybook/react'

import Tag from './Tag'

export default {
  title: 'ui-kit/Tag',
  component: Tag,
}

export const Default: StoryObj<typeof Tag> = {
  args: {
    label: 'Offre collective',
  },
}

export const Closeable: StoryObj<typeof Tag> = {
  args: {
    label: 'Offre collective',
    closeable: {
      onClose: () => {},
      closeLabel: 'Supprimer le tag',
    },
  },
}
