import classnames from 'classnames'
import React from 'react'
import { NavLink } from 'react-router-dom'

import { ROOT_PATH } from '../../utils/config'

const Logo = ({
  className,
  noLink,
  whiteHeader
}) => {
  const src = whiteHeader
    ? `${ROOT_PATH}/icon/app-icon-spotlight.svg`
    : `${ROOT_PATH}/icons/logo-inline-negative.svg`
  const extraProps = {}
  if (noLink) {
    extraProps.onClick = e => e.preventDefault()
  }
  return (
    <NavLink
      className={classnames('logo', className, { 'no-link': noLink })}
      isActive={() => false}
      to='/accueil'
      {...extraProps}>
      <img src={src} alt="Logo" />
    </NavLink>
  )
}

export default Logo
