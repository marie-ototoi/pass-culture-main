import { Position, CroppedRect } from 'react-avatar-editor'

export const croppedRectToPosition = ({
  x,
  y,
  width,
  height,
}: CroppedRect): Position => ({
  x: coordinateToPosition(x, width),
  y: coordinateToPosition(y, height),
})

const coordinateToPosition = (coordonate: number, size: number) =>
  coordonate + size / 2
