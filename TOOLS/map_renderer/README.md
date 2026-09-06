# Map Renderer

Renderer destinado a reconstruir un `.map` de Zircon utilizando las librerías y manifests de este repositorio.

Salida prevista:

- render completo;
- minimapa;
- render de una selección `X0,Y0 -> X1,Y1`;
- reporte de librerías e IDs utilizados.

Nunca sustituirá una tile ausente por una imagen inventada: reportará el recurso que falta.
