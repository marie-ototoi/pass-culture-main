import React from 'react'
import { Outlet } from 'react-router-dom'

import { AppLayout } from 'app/AppLayout'
import SkipLinks from 'components/SkipLinks'
import useActiveFeature from 'hooks/useActiveFeature'
import logoPassCultureProFullIcon from 'icons/logo-pass-culture-pro-full.svg'
import { SvgIcon } from 'ui-kit/SvgIcon/SvgIcon'

import styles from './Signup.module.scss'
import SignupUnavailable from './SignupUnavailable/SignupUnavailable'

export const Signup = () => {
  const isProAccountCreationEnabled = useActiveFeature(
    'ENABLE_PRO_ACCOUNT_CREATION'
  )
  return (
    <>
      <SkipLinks displayMenu={false} />

      <div className={styles['sign-up']}>
        <header className={styles['logo-side']}>
          <SvgIcon
            className="logo-unlogged"
            viewBox="0 0 282 120"
            alt="Pass Culture pro, l’espace des acteurs culturels"
            src={logoPassCultureProFullIcon}
            width="135"
          />
        </header>

        <AppLayout fullscreen pageName="sign-up">
          {isProAccountCreationEnabled ? <Outlet /> : <SignupUnavailable />}
        </AppLayout>
      </div>
    </>
  )
}

// Lazy-loaded by react-router-dom
// ts-unused-exports:disable-next-line
export const Component = Signup
