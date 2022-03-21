import Slider from '@mui/material/Slider'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { styled } from '@mui/material/styles'
import React, { useEffect, useRef, useCallback, useState } from 'react'
import AvatarEditor, { CroppedRect } from 'react-avatar-editor'

import { useEffectUnmount } from 'hooks'

import CanvasTools from './canvas'
import style from './ImageEditor.module.scss'

export interface IImageCropParams {
  croppedRect: CroppedRect
  scale: number
}

const DEFAULT_CROP_BORDER_COLOR = '#fff'
const DEFAULT_IMAGE_CROP_PARAMS: IImageCropParams = {
  croppedRect: {
    x: 0,
    y: 0,
    width: 1,
    height: 1,
  },
  scale: 1,
}

export type OnImageEditorUnmount = ({
  cropParams,
  image,
}: {
  cropParams: IImageCropParams
  image: string
}) => void

export interface IImageEditorProps {
  image: string | File
  canvasHeight: number
  canvasWidth: number
  cropBorderColor?: string
  cropBorderHeight: number
  cropBorderWidth: number
  initialImageCropParams?: IImageCropParams
  onUnmount: OnImageEditorUnmount
  children?: never
}

// croppingRect give us the top left corner of the cropped area
// where AvatarEditor expect the center of it
const coordonateToPosition = (coordonate: number, size: number) =>
  coordonate + size / 2

const ImageEditor = ({
  image,
  canvasHeight,
  canvasWidth,
  cropBorderColor = DEFAULT_CROP_BORDER_COLOR,
  cropBorderHeight,
  cropBorderWidth,
  onUnmount,
  initialImageCropParams = DEFAULT_IMAGE_CROP_PARAMS,
}: IImageEditorProps): JSX.Element => {
  const [scale, setScale] = useState(initialImageCropParams.scale)
  const [position, setPosition] = useState({
    x: coordonateToPosition(
      initialImageCropParams.croppedRect.x,
      initialImageCropParams.croppedRect.width
    ),
    y: coordonateToPosition(
      initialImageCropParams.croppedRect.y,
      initialImageCropParams.croppedRect.height
    ),
  })
  const editorRef = useRef<AvatarEditor>(null)
  const theme = createTheme({
    palette: {
      primary: {
        main: '#eb0055',
        dark: '#eb0055',
        light: '#eb0055',
      },
    },
  })

  // save state in ref to prevents parent re-render to call onUnmount callback only on unmout
  const scaleRef = useRef(scale)

  useEffect(() => {
    scaleRef.current = scale
    console.log('scale: ', scale)
  }, [scale])

  useEffectUnmount(() => {
    console.log('on appelle la callback')
    if (!editorRef.current) return

    const canvas = editorRef.current.getImage()
    const image = canvas.toDataURL()

    const croppedRect = editorRef.current.getCroppingRect()
    console.log('croppingRect: ', croppedRect)
    // croppingRect give us the top left corner of the cropped area
    // where AvatarEditor expect the center of it
    // const coordonateToPosition = (coordonate: number, size: number) =>
    //   coordonate + size / 2
    // const position = {
    //   x: coordonateToPosition(croppingRect.x, croppingRect.width),
    //   y: coordonateToPosition(croppingRect.y, croppingRect.height),
    // }
    onUnmount({
      cropParams: { scale: scaleRef.current, croppedRect },
      image,
    })
  }, [onUnmount])

  const drawCropBorder = useCallback(() => {
    const canvas = document.querySelector('canvas')
    const ctx = canvas?.getContext('2d')
    const canvasTools = new CanvasTools(ctx)
    canvasTools.drawArea({
      width: 0,
      color: cropBorderColor,
      coordinates: [
        cropBorderWidth,
        cropBorderHeight,
        canvasWidth,
        canvasHeight,
      ],
    })
  }, [
    cropBorderColor,
    cropBorderWidth,
    cropBorderHeight,
    canvasWidth,
    canvasHeight,
  ])

  const onScaleChange = useCallback(event => {
    setScale(event.target.value)
  }, [])

  const onPositionChange = useCallback(position => {
    setPosition(position)
  }, [])

  return (
    <div className={style['image-editor']}>
      <AvatarEditor
        border={[cropBorderWidth, cropBorderHeight]}
        color={[0, 0, 0, 0.4]}
        crossOrigin="anonymous"
        height={canvasHeight}
        image={image}
        onImageChange={drawCropBorder}
        onImageReady={drawCropBorder}
        onMouseMove={drawCropBorder}
        onMouseUp={drawCropBorder}
        onPositionChange={onPositionChange}
        position={position}
        ref={editorRef}
        scale={Number(scale)}
        width={canvasWidth}
      />
      <label className={style['image-editor-label']} htmlFor="scale">
        Zoom
      </label>
      <label className={style['image-editor-scale']} htmlFor="scale">
        <span className={style['image-editor-scale-label']}>min</span>
        <span className={style['image-editor-scale-input']}>
          <ThemeProvider theme={theme}>
            <CustomSlider
              max={4}
              min={1}
              onChange={onScaleChange}
              step={0.01}
              value={scale}
            />
          </ThemeProvider>
        </span>
        <span className={style['image-editor-scale-label']}>max</span>
      </label>
    </div>
  )
}
const CustomSlider = styled(Slider)(() => ({
  '& .MuiSlider-thumb': {
    height: 16,
    width: 16,
  },
}))
ImageEditor.displayName = 'ImageEditor'

export default ImageEditor
