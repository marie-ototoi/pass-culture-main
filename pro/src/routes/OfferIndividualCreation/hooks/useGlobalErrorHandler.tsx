import React from 'react'
import { useHistory } from 'react-router-dom'

import { useHomePath } from 'hooks'
import useNotification from 'components/hooks/useNotification'

const useGlobalErrorHandler = (): ((errorMessage: string) => void) => {
  const homePath = useHomePath()
  const notify = useNotification()
  const history = useHistory()

  return (errorMessage: string) => {
    if (errorMessage) {
      notify.error(errorMessage)
      history.push(homePath)
    }
  }
}

export default useGlobalErrorHandler
