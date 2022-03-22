import React, { useCallback, useState } from 'react'
import { CroppedRect } from 'react-avatar-editor'

import { getDataURLFromImageURL } from 'api/utils/api'
import useNotification from 'components/hooks/useNotification'
import { imageConstraints } from 'new_components/ConstraintCheck/imageConstraints'
import DialogBox from 'new_components/DialogBox'
import { postImageToVenue } from 'repository/pcapi/pcapi'

import { ImportFromComputer } from '../ImportFromComputer/ImportFromComputer'
import { VenueImageEdit } from '../VenueImageEdit/VenueImageEdit'
import { VenueImagePreview } from '../VenueImagePreview/VenueImagePreview'

import { IMAGE_TYPES, MAX_IMAGE_SIZE, MIN_IMAGE_WIDTH } from './constants'
import {
  IImageCropParams,
  OnImageEditorUnmount,
} from 'new_components/ImageEditor/ImageEditorNew'

interface IVenueImageUploaderModalProps {
  venueId: string
  onDismiss: () => void
  venueCredit: string
  onImageUpload: ({
    bannerUrl,
    credit,
  }: {
    bannerUrl: string
    credit: string
  }) => void
  defaultImage?: string
}

const constraints = [
  imageConstraints.formats(IMAGE_TYPES),
  imageConstraints.size(MAX_IMAGE_SIZE),
  imageConstraints.width(MIN_IMAGE_WIDTH),
]

export const VenueImageUploaderModal = ({
  venueId,
  onDismiss,
  defaultImage,
  venueCredit,
  onImageUpload,
}: IVenueImageUploaderModalProps): JSX.Element => {
  const [image, setImage] = useState<string | undefined>(defaultImage)
  const [credit, setCredit] = useState(venueCredit)
  const [croppedRect, setCroppedRect] = useState<CroppedRect>({
    x: 0.5,
    y: 0.5,
    width: 1,
    height: 1,
  })
  const [editedImage, setEditedImage] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [editorInitialScale, setEditorInitialScale] = useState(1)
  const notification = useNotification()

  const onSetImage = useCallback(
    file => {
      setImage(file)
    },
    [setImage]
  )

  const onEditedImageSave = useCallback<OnImageEditorUnmount>(
    ({ cropParams, getImageCallback }) => {
      setCroppedRect(cropParams.croppedRect)
      setEditorInitialScale(cropParams.scale)
      setEditedImage(getImageCallback())
    },
    [setEditedImage, setCroppedRect]
  )

  const navigateFromPreviewToEdit = useCallback(() => {
    setEditedImage('')
  }, [])

  const onReplaceImage = useCallback(() => {
    setImage(undefined)
  }, [setImage])

  const onUpload = useCallback(async () => {
    if (typeof croppedRect === undefined) return
    if (typeof image === undefined) return

    try {
      setIsUploading(true)
      // the request needs the dataURL of the image,
      // so we need to retrieve it if we only have the URL
      const imageDataURL =
        typeof image === 'string' ? await getDataURLFromImageURL(image) : image
      const { bannerUrl } = await postImageToVenue({
        venueId,
        banner: imageDataURL,
        xCropPercent: croppedRect?.x,
        yCropPercent: croppedRect?.y,
        heightCropPercent: croppedRect?.height,
        imageCredit: credit,
      })
      onImageUpload({ bannerUrl, credit })
      setIsUploading(false)
      onDismiss()
      notification.success('Vos modifications ont bien été prises en compte')
    } catch {
      notification.error(
        'Une erreur est survenue lors de la sauvegarde de vos modifications.\n Merci de réessayer plus tard'
      )
      setIsUploading(false)
    }
  }, [
    venueId,
    image,
    croppedRect,
    onDismiss,
    notification,
    credit,
    onImageUpload,
  ])

  return (
    <DialogBox
      hasCloseButton
      labelledBy="Ajouter une image"
      onDismiss={onDismiss}
    >
      {!image ? (
        <ImportFromComputer
          constraints={constraints}
          imageTypes={IMAGE_TYPES}
          onSetImage={onSetImage}
          orientation="landscape"
        />
      ) : !croppedRect || !editedImage ? (
        <VenueImageEdit
          credit={credit}
          image={image}
          initialCropParams={{
            croppedRect,
            scale: editorInitialScale,
          }}
          onEditedImageSave={onEditedImageSave}
          onReplaceImage={onReplaceImage}
          onSetCredit={setCredit}
          // saveInitialPosition={setEditorInitialPosition}
          // saveInitialScale={setEditorInitialScale}
        />
      ) : (
        <VenueImagePreview
          isUploading={isUploading}
          onGoBack={navigateFromPreviewToEdit}
          onUploadImage={onUpload}
          preview={editedImage}
          withActions
        />
      )}
    </DialogBox>
  )
}
VenueImageUploaderModal.whyDidYouRender = true
