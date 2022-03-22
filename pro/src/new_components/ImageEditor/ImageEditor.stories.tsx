import { Story } from '@storybook/react'
import React from 'react'

import { ImageEditor, IImageEditorProps } from './ImageEditorNew'
import sampleImage from './sample-image.jpg'

export default {
  title: 'components/ImageEditor',
  component: ImageEditor,
}

const Template: Story<IImageEditorProps> = props => (
  <>
    <ImageEditor {...props} />
    <h1>
      Ne pas cliquer sur l'onglet "DOCS" de ce storybook, car il ne fonctionne
      pas.
    </h1>
  </>
)

export const Default = Template.bind({})
Default.args = {
  canvasHeight: 300,
  canvasWidth: 400,
  cropBorderColor: '#FFF',
  cropBorderHeight: 30,
  cropBorderWidth: 40,
  image: sampleImage,
}

export const WithInitialScale = Template.bind({})
WithInitialScale.args = {
  canvasHeight: 300,
  canvasWidth: 400,
  cropBorderColor: '#FFF',
  cropBorderHeight: 30,
  cropBorderWidth: 40,
  image: sampleImage,
  initialImageCropParams: {
    croppedRect: {
      x: 0.25,
      y: 0.3716700819672131,
      width: 0.5,
      height: 0.2566598360655738,
    },
    scale: 1.5,
  },
}

export const WithInitialPosition = Template.bind({})
WithInitialPosition.args = {
  canvasHeight: 300,
  canvasWidth: 400,
  cropBorderColor: '#FFF',
  cropBorderHeight: 30,
  cropBorderWidth: 40,
  image: sampleImage,
  initialImageCropParams: {
    croppedRect: {
      x: 0,
      y: 0,
      width: 0.5,
      height: 0.2566598360655738,
    },
    scale: 1.5,
  },
}
