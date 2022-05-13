import Divider from './Divider'
import React from 'react'

export default {
  title: 'ui-kit/Divider',
  component: Divider,
}

const Template = args => (
  <div>
    <p>Second text</p>
    <Divider {...args} />
    <p>Second text</p>
  </div>
)

export const Default = Template.bind({})

Default.args = {
  size: 'medium',
}
