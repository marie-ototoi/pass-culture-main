import { useEffect } from 'react'

const useEffectUnmount = (callback: () => void, deps: unknown[] = []): void => {
  useEffect(
    () => () => callback(),
    deps // eslint-disable-line react-hooks/exhaustive-deps
  )
}

export default useEffectUnmount
