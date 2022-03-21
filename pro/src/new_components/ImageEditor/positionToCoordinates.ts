export const positionToCoordinates = ()  => {}


/*
CroppedRect : croppingRect.x, croppingRect.width, croppingRect.y, croppingRect.height

croppingRect.x,y -> position du coin haut-gauche du rectangle de crop
croppingRect.x ~ position.x - 0.5 * fn(scale)

croppingRect.width = 1 / scale
croppingRect.height = 1 / scale * RATIO ?


CropParams : position.x, position.y, scale, ??
position.x -> position centrée
*/