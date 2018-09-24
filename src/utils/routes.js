import React from 'react'
import { Redirect } from 'react-router-dom'

import BetaPage from '../components/pages/BetaPage'
import BookingsPage from '../components/pages/BookingsPage'
import DiscoveryPage from '../components/pages/DiscoveryPage'
import FavoritesPage from '../components/pages/FavoritesPage'
import ForgottenPage from '../components/pages/ForgottenPage'
import ProfilePage from '../components/pages/ProfilePage'
import SearchPage from '../components/pages/SearchPage'
import SigninPage from '../components/pages/SigninPage'
import SignupPage from '../components/pages/SignupPage'
import TermsPage from '../components/pages/TermsPage'

// NOTE: la gestion des éléments du menu principal
// se fait dans le fichier src/components/MainMenu
const routes = [
  {
    path: '/',
    render: () => <Redirect to="/beta" />,
  },
  {
    component: BetaPage,
    path: '/beta',
    title: "Bienvenue dans l'avant-première du Pass Culture",
  },
  {
    component: SigninPage,
    path: '/connexion',
    title: 'Connexion',
  },
  {
    component: SignupPage,
    path: '/inscription',
    title: 'Inscription',
  },
  {
    component: ForgottenPage,
    path: '/mot-de-passe-perdu/:view?',
    title: 'Mot de passe perdu',
  },
  /* ---------------------------------------------------
   *
   * MENU ITEMS
   * NOTE les elements ci-dessous sont les elements du main menu
   * Car ils contiennent une propriété `icon`
   *
   ---------------------------------------------------  */
  {
    component: DiscoveryPage,
    disabled: false,
    icon: 'offres-w',
    // exemple d'URL optimale qui peut être partagée
    // par les sous composants
    path: '/decouverte/:offerId?/:mediationId?/:view(booking|verso)?',
    title: 'Les offres',
  },
  {
    component: SearchPage,
    disabled: false,
    icon: 'search-w',
    path: '/recherche/:view(categories|resultats)?/:filtres?',
    title: 'Recherche',
  },
  {
    component: BookingsPage,
    disabled: false,
    icon: 'calendar-w',
    path: '/reservations',
    title: 'Mes Réservations',
  },
  {
    component: FavoritesPage,
    disabled: true,
    icon: 'like-w',
    path: '/favoris',
    title: 'Mes Préférés',
  },
  {
    component: ProfilePage,
    disabled: false,
    icon: 'user-w',
    path: '/profil/:view?/:status?',
    title: 'Mon Profil',
  },
  {
    disabled: false,
    href: 'mailto:pass@culture.gouv.fr',
    icon: 'mail-w',
    title: 'Nous contacter',
  },
  {
    component: TermsPage,
    disabled: false,
    icon: 'txt-w',
    path: '/mentions-legales',
    title: 'Mentions Légales',
  },
]

export default routes
