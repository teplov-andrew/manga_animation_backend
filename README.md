# manga_animation_backend

## Донастройка до полного репозиторий
Для того чтобы работал эндпоинт `/colorize/`, нужно создать папку `colorizer` и поместить в нее содержимое [данного репозитория](https://github.com/qweasdd/manga-colorization-v2), также скачать веса моделей про которые подробно описано в README [данного репозитория](https://github.com/qweasdd/manga-colorization-v2).

Также нужно создать файл `.env`, в который нужно поместить данные в таком формате:
```
FAL_KEY="YOUR_KEY"
ACCESS_KEY="YOUR_KEY"
SECRET_KEY="YOUR_KEY"
BUCKET_NAME="YOUR_KEY"
```
## Загрузка дообученного чекпоинта для CogVideoX
Для начала нужно склонировать [репозиторий CogVideoX](https://github.com/THUDM/CogVideo.git), после скачивай [чекпоинт](https://drive.google.com/file/d/1puQkkfIQLy1D3tn1rvCm6CLDoevOp76G/view?usp=sharing) и помещаем в папку `CogVideo/checkpoint`
