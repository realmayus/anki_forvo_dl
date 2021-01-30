# anki-forvo-dl
<b>An add-on that allows you to (bulk-) add <a href="http://Forvo.com" rel="nofollow">Forvo.com</a> pronunciations to your anki cards - fully automatically</b>

The add-on has two modes:
<ul>
<li>A single-add mode</li>
<li>A bulk-add mode</li>
</ul>

## Download
You can download the plugin using anki. Open the add-on manager by clicking Tools > Add-ons and press "Get Add-ons...".

Then paste this code in the window: `858591644`

The add-on's download page can be found here: https://ankiweb.net/shared/info/858591644

## Guide
<b>Using the single-add mode</b>
When you add or edit a card, you will notice the blue Forvo button in the editor window. If you click that, anki-forvo-dl will ask you to select some fields and a language if not done already.
Afterwards, you will be presented with a dialog window that shows you a list of all available pronunciations. If you click on the play button on the left of a pronunciation, you can listen to the audio. To select a pronunciation, click the checkmark icon.

<b>Using the bulk-add mode</b>
The power of anki-forvo-dl is the bulk-add mode: Select your cards and lean back while letting the add-on do its job. 
In order to select your cards, go to the card browser and select all the ones you wish to add audio to. Right click on the selection and choose "Bulk add Forvo audio to X cards". A dialog will pop up.
If anki-forvo-dl doesn't know the fields and/or languages of the selected cards already, you will be prompted to select the fields for every note type your selected cards use and will be asked to select the language for all decks that are unknown to anki-forvo-dl. Because you can cards from multiple decks and note types in the browser, it is possible that you will have to do this multiple times to address all different note types and languages.

<b>Field selection</b>
When adding audio to a card with a note type for the first time, anki-forvo-dl will ask you to select two fields:
The search field, whose contents will be used to search on Forvo and the audio field, where the audio string will be placed in ([audio:XYZ.mp3]).
By default, anki-forvo-dl will append the audio string to the existing contents of the audio field. If you want to change that, see the "Editing the config" section.

<b>Language selection</b>
When adding audio to a card that's part of a deck that isn't known by anki-forvo-dl, it will ask you to select the deck's language so that only relevant pronunciations will be available as results. You can either type in the language in English and hit enter or select it from the list you will be presented with. If you want to change the language later, see the "Editing the config" section

<b>Editing the config</b>
<b>Note:</b> As of now, you will have to edit the config manually. To do that, go to Tools &gt; Add-ons &gt; Select anki_forvo_dl &gt; View Files. Then open the user_files directory and open the config.json file.

<b>Liability</b>
I am not liable for the plugin to work as described or for the downloads. Please create a backup of your anki folder before using it (just in case!)
For the license, see: <a href="https://github.com/realmayus/anki_forvo_dl/blob/main/LICENSE" rel="nofollow">https://github.com/realmayus/anki_forvo_dl/blob/main/LICENSE</a>
The source code is available here: <a href="https://github.com/realmayus/anki_forvo_dl" rel="nofollow">https://github.com/realmayus/anki_forvo_dl</a>

<b>Please only report bugs through the <a href="https://github.com/realmayus/anki_forvo_dl/issues" rel="nofollow">GitHub issue tracker</a>, NOT through reviews.</b>
If you have questions, comments or feedback, you can post it here: <a href="https://github.com/realmayus/anki_forvo_dl/discussions" rel="nofollow">https://github.com/realmayus/anki_forvo_dl/discussions</a>

