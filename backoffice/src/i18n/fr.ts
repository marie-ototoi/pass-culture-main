import { all } from 'deepmerge'
import ra from 'ra-language-french'
import { TranslationMessages } from 'react-admin'

const messages = all([ra]) as TranslationMessages

export default messages
