# anki-forvo-dl
<b>An add-on that allows you to add <a href="http://Forvo.com" rel="nofollow">Forvo.com</a> pronunciations to your anki cards - fully automatically</b>

## Download
You can download the plugin using anki. Open the add-on manager by clicking Tools > Add-ons and press "Get Add-ons...".

Then paste this code in the window: `858591644`

The add-on's download page can be found here: https://ankiweb.net/shared/info/858591644

## Guide

<b>Usage</b>

When you add or edit a card, you will notice the blue Forvo button in the editor window. If you click that, anki-forvo-dl will ask you to select some fields and a language if not done already.
Afterwards, you will be presented with a dialog window that shows you a list of all available pronunciations. If you click on the play button on the left of a pronunciation, you can listen to the audio. To select a pronunciation, click the checkmark icon.

You can also hold down the shift key when pressing the blue Forvo button in the editor to automatically select the pronunciation with the most votes.
Other shortcuts:
- ctrl + F: Open forvo window
- ctrl + shift + F: Add top pronunciation


<b>Field selection</b>

When adding audio to a card with a note type for the first time, anki-forvo-dl will ask you to select two fields:
The search field, whose contents will be used to search on Forvo and the audio field, where the audio string will be placed in ([audio:XYZ.mp3]).
By default, anki-forvo-dl will append the audio string to the existing contents of the audio field. If you want to change that, see the "Editing the config" section.

<b>Language selection</b>

When adding audio to a card that's part of a deck that isn't known by anki-forvo-dl, it will ask you to select the deck's language so that only relevant pronunciations will be available as results. You can either type in the language in English and hit enter or select it from the list you will be presented with. If you want to change the language later, see the "Editing the config" section

<b>Editing the config</b>

As of the newest version, there's a config manager! Just click on Tools>anki-forvo-dl>Preferences to open it. For deck-specific or note type-specific settings select your deck / note type first and adjust the settings to your liking.

<b>Liability</b>

I am not liable for the plugin to work as described or for the actual download process. This plugin retrieves the audio files as if you would click on the audio preview button on Forvo, which falls under web scraping. Forvo doesn't mention web scraping in their Terms of Service so I believe that this is allowed, since it's as if you'd go there manually, just automated.
Please create a backup of your anki folder before using it (just in case!)
For the license, see: <a href="https://github.com/realmayus/anki_forvo_dl/blob/main/LICENSE" rel="nofollow">https://github.com/realmayus/anki_forvo_dl/blob/main/LICENSE</a>
The source code is available here: <a href="https://github.com/realmayus/anki_forvo_dl" rel="nofollow">https://github.com/realmayus/anki_forvo_dl</a>

<b>Please only report bugs through the <a href="https://github.com/realmayus/anki_forvo_dl/issues" rel="nofollow">GitHub issue tracker</a>, NOT through reviews.</b>
If you have questions, comments or feedback, you can post it here: <a href="https://github.com/realmayus/anki_forvo_dl/discussions" rel="nofollow">https://github.com/realmayus/anki_forvo_dl/discussions</a>


