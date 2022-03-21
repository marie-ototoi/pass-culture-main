import React, { useCallback, useRef, useState } from 'react'
import AvatarEditor from 'react-avatar-editor'

import useNotification from 'components/hooks/useNotification'
import { ReactComponent as DownloadIcon } from 'icons/ico-download-filled.svg'
import { CreditInput } from 'new_components/CreditInput/CreditInput'
import ImageEditor, {
  IImageCropParams,
  OnImageEditorUnmount,
} from 'new_components/ImageEditor/ImageEditorNew'
import { Button, Divider } from 'ui-kit'
import { ButtonVariant } from 'ui-kit/Button/types'

import style from './VenueImageEdit.module.scss'

const CANVAS_HEIGHT = 244
const CANVAS_WIDTH = (CANVAS_HEIGHT * 3) / 2
const CROP_BORDER_HEIGHT = 40
const CROP_BORDER_WIDTH = 100
const CROP_BORDER_COLOR = '#fff'

interface IVenueImageEditProps {
  image: string | File
  credit: string
  onSetCredit: (credit: string) => void
  children?: never
  onReplaceImage: () => void
  initialCropParams: IImageCropParams
  onEditedImageSave: OnImageEditorUnmount
}

export const VenueImageEdit = ({
  onReplaceImage,
  image,
  credit,
  onSetCredit,
  onEditedImageSave,
  initialCropParams,
}: IVenueImageEditProps): JSX.Element => {
  const editorRef = useRef<AvatarEditor>(null)
  const notification = useNotification()

  const [displayEditor, setDisplayEditor] = useState(true)

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      // handleNext()
    }
  }

  // notification.error(
  //   'Une erreur est survenue. Merci de réessayer plus tard'

  return (
    <section className={style['venue-image-edit']}>
      <form action="#" className={style['venue-image-edit-form']}>
        <header>
          <h1 className={style['venue-image-edit-header']}>Image du lieu</h1>
        </header>
        <p className={style['venue-image-edit-right']}>
          En utilisant ce contenu, je certifie que je suis propriétaire ou que
          je dispose des autorisations nécessaires pour l’utilisation de
          celui-ci.
        </p>
        {displayEditor && (
          <ImageEditor
            canvasHeight={CANVAS_HEIGHT}
            canvasWidth={CANVAS_WIDTH}
            cropBorderColor={CROP_BORDER_COLOR}
            cropBorderHeight={CROP_BORDER_HEIGHT}
            cropBorderWidth={CROP_BORDER_WIDTH}
            image={image}
            initialImageCropParams={initialCropParams}
            onUnmount={onEditedImageSave}
          />
        )}
        <CreditInput
          credit={credit}
          extraClassName={style['venue-image-edit-credit']}
          onKeyDown={onKeyDown}
          updateCredit={onSetCredit}
        />
      </form>
      <Divider />
      <footer className={style['venue-image-edit-footer']}>
        <Button
          Icon={DownloadIcon}
          onClick={onReplaceImage}
          variant={ButtonVariant.TERNARY}
        >
          Remplacer l'image
        </Button>
        <Button
          onClick={() => {
            setDisplayEditor(false)
          }}
        >
          Suivant
        </Button>
      </footer>
    </section>
  )
}
