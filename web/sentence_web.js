/*
Every sentence:

<div class="sentenceWidget">
    <button>Play</button>
    <div class="sentenceContent">
        <p class="sentence">{Some sentence, with <ruby>tags</ruby>}</p>
        <p class="translation">{translation}</p>
        <p class="details">{some details; author; location etc.}</p>
    <div>
    <button>Add</button>
</div>
 */

function setup(sentences, images) {
    // sentences is a JSON array. parse it
    const sentences_js = JSON.parse(sentences);
    const body = document.querySelector('body');
    const list = document.createElement("div");
    list.classList.add("list");
    for (const sentence of sentences_js) {
        const sentenceWidget = document.createElement('div');
        sentenceWidget.classList.add('sentenceWidget');


        const sentenceContent = document.createElement("div");
        sentenceContent.classList.add('sentenceContent');

        const sentenceElement = document.createElement('p');
        sentenceElement.classList.add('sentence');
        sentenceElement.innerHTML = sentence.transcription ? sentence.transcription : sentence.text_orig;

        const translationElement = document.createElement('p');
        translationElement.classList.add('translation');
        translationElement.innerHTML = sentence.text_translation;

        const detailsElement = document.createElement('p');
        detailsElement.classList.add('details');
        detailsElement.innerHTML = "Sentence author: " + sentence.author;

        const addButton = document.createElement('button');
        addButton.classList.add('addBtn');
        addButton.onclick = () => {
            pycmd(`add:${sentence.id}`);
        }
        const addButtonImg = document.createElement("img");
        addButtonImg.src = images[1];
        addButton.appendChild(addButtonImg);

        if (sentence.has_audio) {
            const playButton = document.createElement('button');
            playButton.classList.add('playBtn');
            playButton.onclick = () => {
                pycmd(`play:${sentence.id}`);
            }
            const playButtonImg = document.createElement("img");
            playButtonImg.src = images[0];
            playButton.appendChild(playButtonImg);

            sentenceWidget.appendChild(playButton);
        }
        sentenceContent.appendChild(sentenceElement);
        sentenceContent.appendChild(translationElement);
        sentenceContent.appendChild(detailsElement);
        sentenceWidget.appendChild(sentenceContent);
        sentenceWidget.appendChild(addButton);
        list.appendChild(sentenceWidget);
    }
    body.appendChild(list);
}