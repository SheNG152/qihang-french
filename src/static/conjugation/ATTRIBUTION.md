# French pronunciation audio

These MP3 clips were generated for the French Conjugation Trainer using Piper
and the `fr_FR-siwis-medium` voice. They are synthesized speech, not original
recordings of the speaker or endorsements by the dataset authors.

Voice model: Michael Hansen / Rhasspy, `fr_FR-siwis-medium`.
https://huggingface.co/rhasspy/piper-voices/tree/main/fr/fr_FR/siwis/medium
Model SHA-256: 641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99
The model card identifies the SIWIS dataset license as CC BY 4.0.

Dataset citation:
Junichi Yamagishi, Pierre-Edouard Honnet, Philip Garner, and Alexandros Lazaridis
(2017). The SIWIS French Speech Synthesis Database, 2016. University of Edinburgh.
https://doi.org/10.7488/ds/1705

Generation: Piper 1.8.0, SIWIS medium, length_scale 1.1, 22,050 Hz mono;
encoded as 48 kbps MP3 using lameenc 1.8.1.
Source texts come from this application's conjugation wordlists.
Changes: synthesized new speech from these texts, added pronouns and elision,
converted the generated waveform to MP3, and assigned content-based filenames.

These generated audio assets are distributed under Creative Commons Attribution
4.0 International (CC BY 4.0). Retain this attribution when redistributing them.
https://creativecommons.org/licenses/by/4.0/

Piper and its model are build-time tools and are not included in the app packages.
