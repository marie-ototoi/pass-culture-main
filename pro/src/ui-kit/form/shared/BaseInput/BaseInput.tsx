import cn from 'classnames'
import React, { ForwardedRef, forwardRef } from 'react'

import styles from './BaseInput.module.scss'

interface IBaseInputProps
  extends Partial<React.InputHTMLAttributes<HTMLInputElement>> {
  className?: string
  hasError?: boolean
  RightIcon?: React.FunctionComponent<
    React.SVGProps<SVGSVGElement> & {
      title?: string | undefined
    }
  >
  RightButton?: React.FunctionComponent<
    React.SVGProps<SVGSVGElement> & {
      title?: string | undefined
    }
  >
  onButtonClick?: (e: React.MouseEvent<HTMLElement>) => void
}

const BaseInput = forwardRef(
  (
    { className, hasError, name, RightIcon, RightButton, onButtonClick, ...props }: IBaseInputProps,
    ref: ForwardedRef<HTMLInputElement>
  ): JSX.Element => {
    if (RightIcon) {
      return (
        <div className={styles['base-input-wrapper']}>
          <input
            {...props}
            aria-invalid={hasError}
            className={cn(
              styles['base-input'],
              styles['base-input-with-right-icon'],
              {
                [styles['has-error']]: hasError,
              },
              className
            )}
            name={name}
            ref={ref}
          />
          <span className={styles['base-input-right-icon']}>
            <RightIcon />
          </span>
        </div>
      )
    }
    else if (RightButton) {
      return (
        <div className={styles['base-input-wrapper']}>
          <input
            {...props}
            aria-invalid={hasError}
            className={cn(
              styles['base-input'],
              styles['base-input-with-right-button'],
              {
                [styles['has-error']]: hasError,
              },
              className
            )}
            name={name}
            ref={ref}
          />
          <button onClick={onButtonClick} className={styles['base-input-right-button']}>
            <RightButton />
          </button>
        </div>
      )
    }
    else {
      return (
        <input
          {...props}
          aria-invalid={hasError}
          className={cn(
            styles['base-input'],
            {
              [styles['has-error']]: hasError,
            },
            className
          )}
          id={name}
          name={name}
          ref={ref}
        />
      )
    }
  }
)
BaseInput.displayName = 'BaseInput'
export default BaseInput
