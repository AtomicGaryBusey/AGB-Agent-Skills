# WCAG 2.2 success criteria — Principle 1: Perceivable

> **Source and licence.** Normative text quoted in this file (marked as block quotes, including SC text, notes and guideline statements) is copied verbatim from
> *Web Content Accessibility Guidelines (WCAG) 2.2*, W3C Recommendation, 12 December 2024 edition,
> <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide Web Consortium.
> <https://www.w3.org/copyright/document-license-2023/>. Status: W3C Recommendation.
> Technique and failure IDs/titles and ACT rule names are taken from *Understanding WCAG 2.2* and
> *Techniques for WCAG 2.2* (W3C Group Notes, informative), <https://www.w3.org/WAI/WCAG22/Understanding/>,
> <https://www.w3.org/WAI/WCAG22/Techniques/>, Copyright © 2024 World Wide Web Consortium, under the same licence.
> All other text (summaries, testability, procedures, code patterns and examples) is original to this skill.
> See `NOTICE` at the skill root.

Principle 1 has 29 success-criterion sections. Each entry uses the check ID `WCAG-<sc>` (see `check-index.md`). Testability: **automated** = a tool can decide the core requirement for most content; **assisted** = tools find candidates or partial failures and a human confirms; **manual** = human judgement dominates. "Static scanner" means the skill's source-code scanner; "page runner" means the live-page runner (axe-core 4.13.0 plus custom checks).

## Contents

- Guideline 1.1 Text Alternatives
  - [WCAG-1.1.1 Non-text Content](#wcag-1-1-1) (A)
- Guideline 1.2 Time-based Media
  - [WCAG-1.2.1 Audio-only and Video-only (Prerecorded)](#wcag-1-2-1) (A)
  - [WCAG-1.2.2 Captions (Prerecorded)](#wcag-1-2-2) (A)
  - [WCAG-1.2.3 Audio Description or Media Alternative (Prerecorded)](#wcag-1-2-3) (A)
  - [WCAG-1.2.4 Captions (Live)](#wcag-1-2-4) (AA)
  - [WCAG-1.2.5 Audio Description (Prerecorded)](#wcag-1-2-5) (AA)
  - [WCAG-1.2.6 Sign Language (Prerecorded)](#wcag-1-2-6) (AAA)
  - [WCAG-1.2.7 Extended Audio Description (Prerecorded)](#wcag-1-2-7) (AAA)
  - [WCAG-1.2.8 Media Alternative (Prerecorded)](#wcag-1-2-8) (AAA)
  - [WCAG-1.2.9 Audio-only (Live)](#wcag-1-2-9) (AAA)
- Guideline 1.3 Adaptable
  - [WCAG-1.3.1 Info and Relationships](#wcag-1-3-1) (A)
  - [WCAG-1.3.2 Meaningful Sequence](#wcag-1-3-2) (A)
  - [WCAG-1.3.3 Sensory Characteristics](#wcag-1-3-3) (A)
  - [WCAG-1.3.4 Orientation](#wcag-1-3-4) (AA)
  - [WCAG-1.3.5 Identify Input Purpose](#wcag-1-3-5) (AA)
  - [WCAG-1.3.6 Identify Purpose](#wcag-1-3-6) (AAA)
- Guideline 1.4 Distinguishable
  - [WCAG-1.4.1 Use of Color](#wcag-1-4-1) (A)
  - [WCAG-1.4.2 Audio Control](#wcag-1-4-2) (A)
  - [WCAG-1.4.3 Contrast (Minimum)](#wcag-1-4-3) (AA)
  - [WCAG-1.4.4 Resize Text](#wcag-1-4-4) (AA)
  - [WCAG-1.4.5 Images of Text](#wcag-1-4-5) (AA)
  - [WCAG-1.4.6 Contrast (Enhanced)](#wcag-1-4-6) (AAA)
  - [WCAG-1.4.7 Low or No Background Audio](#wcag-1-4-7) (AAA)
  - [WCAG-1.4.8 Visual Presentation](#wcag-1-4-8) (AAA)
  - [WCAG-1.4.9 Images of Text (No Exception)](#wcag-1-4-9) (AAA)
  - [WCAG-1.4.10 Reflow](#wcag-1-4-10) (AA)
  - [WCAG-1.4.11 Non-text Contrast](#wcag-1-4-11) (AA)
  - [WCAG-1.4.12 Text Spacing](#wcag-1-4-12) (AA)
  - [WCAG-1.4.13 Content on Hover or Focus](#wcag-1-4-13) (AA)

## Guideline 1.1 — Text Alternatives

> Provide text alternatives for any non-text content so that it can be changed into other forms people need, such as large print, braille, speech, symbols or simpler language.

<a id="wcag-1-1-1"></a>
### WCAG-1.1.1 — Non-text Content (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#non-text-content> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html>

- **Text:**

  > All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.
  >
  > - **Controls, Input:** If non-text content is a control or accepts user input, then it has a name that describes its purpose. (Refer to Success Criterion 4.1.2 for additional requirements for controls and content that accepts user input.)
  > - **Time-Based Media:** If non-text content is time-based media, then text alternatives at least provide descriptive identification of the non-text content. (Refer to Guideline 1.2 for additional requirements for media.)
  > - **Test:** If non-text content is a test or exercise that would be invalid if presented in text, then text alternatives at least provide descriptive identification of the non-text content.
  > - **Sensory:** If non-text content is primarily intended to create a specific sensory experience, then text alternatives at least provide descriptive identification of the non-text content.
  > - **CAPTCHA:** If the purpose of non-text content is to confirm that content is being accessed by a person rather than a computer, then text alternatives that identify and describe the purpose of the non-text content are provided, and alternative forms of CAPTCHA using output modes for different types of sensory perception are provided to accommodate different disabilities.
  > - **Decoration, Formatting, Invisible:** If non-text content is pure decoration, is used only for visual formatting, or is not presented to users, then it is implemented in a way that it can be ignored by assistive technology.

- **Applies to:** images, icons, SVG, canvas, image buttons, image maps, charts, CAPTCHA, emoji/ASCII art, decorative images
- **Testability:** assisted — axe-core (image-alt, input-image-alt, object-alt, role-img-alt, svg-img-alt, aria-meter-name, aria-progressbar-name) catches missing names but cannot judge whether a text alternative is equivalent. A static scanner can flag `<img>` without `alt`, `alt` equal to a filename, and icon-only buttons; a page runner can list every rendered image with its computed accessible name for a human to review.
  - **axe-core rules (4.13.0):** `aria-meter-name`, `aria-progressbar-name`, `image-alt`, `input-image-alt`, `object-alt`, `role-img-alt`, `svg-img-alt`
- **Test procedure:**
  1. Inventory all non-text content: `<img>`, `<svg>`, `<canvas>`, CSS background images that convey meaning, icon fonts, `<input type="image">`, `<area>`, `<object>`.
  2. For each, obtain the computed accessible name (browser devtools accessibility pane or a screen reader).
  3. Judge whether the name conveys the same information or function in context; for controls, check it names the purpose, not the picture.
  4. Confirm decorative images are hidden from AT (`alt=""`, `aria-hidden="true"`, or CSS background) and informative ones are not.
  5. For complex images (charts, diagrams), confirm a long description exists nearby or is linked.
  6. For CAPTCHA, confirm a text label describing its purpose and an alternative modality exist.
- **Common failures:**
  - F3 — Failure of Success Criterion 1.1.1 due to conveying information exclusively using CSS background images
  - F13 — Failure of Success Criterion 1.1.1 and 1.4.1 due to having a text alternative that does not include information that is conveyed by color differences in the image
  - F20 — Failure of Success Criterion 1.1.1 and 4.1.2 due to not updating text alternatives when changes to non-text content occur
  - F30 — Failure of Success Criterion 1.1.1 and 1.2.1 due to using text alternatives that are not alternatives (e.g., filenames or placeholder text)
  - F38 — Failure of Success Criterion 1.1.1 due to not marking up decorative images in HTML in a way that allows assistive technology to ignore them
  - F39 — Failure of Success Criterion 1.1.1 due to providing a text alternative that is not null (e.g., alt="spacer" or alt="image") for images that should be ignored by assistive technology
  - F65 — Failure of Success Criterion 1.1.1 due to omitting the alt attribute or text alternative on img elements, area elements, and input elements of type "image"
  - F67 — Failure of Success Criterion 1.1.1 and 1.2.1 due to providing long descriptions for non-text content that does not serve the same purpose or does not present the same information
  - F71 — Failure of Success Criterion 1.1.1 due to using text look-alikes to represent text without providing a text alternative
  - F72 — Failure of Success Criterion 1.1.1 due to using ASCII art without providing a text alternative
  - Pattern: `<img src="chart.png">` with no `alt` attribute, so screen readers announce the file name.
  - Pattern: Icon-only control such as `<button><svg>...</svg></button>` with no `aria-label` or hidden text.
  - Pattern: `alt` text that is a filename, a placeholder (`alt="image"`) or duplicates adjacent link text.
  - Pattern: Decorative image given descriptive `alt`, or meaningful image given `alt=""` / `role="presentation"`.
  - Pattern: `<svg role="img">` without `<title>` or `aria-label`; React `<img alt={undefined}>`.
- **Sufficient techniques:**
  - G94 — Providing short text alternative for non-text content that serves the same purpose and presents the same information as the non-text content
  - ARIA6 — Using aria-label to provide labels for objects
  - ARIA10 — Using aria-labelledby to provide a text alternative for non-text content
  - G196 — Using a text alternative on one item within a group of images that describes all items in the group
  - H2 — Combining adjacent image and text links for the same resource
  - H37 — Using alt attributes on img elements
  - H53 — Using the body of the object element
  - H86 — Providing text alternatives for emojis, emoticons, ASCII art, and leetspeak
  - PDF1 — Applying text alternatives to images with the Alt entry in PDF documents
  - G95 — Providing short text alternatives that provide a brief description of the non-text content
  - ARIA15 — Using aria-describedby to provide descriptions of images
  - G73 — Providing a long description in another location with a link to it that is immediately adjacent to the non-text content
  - G74 — Providing a long description in text near the non-text content, with a reference to the location of the long description in the short description
  - G92 — Providing long description for non-text content that serves the same purpose and presents the same information
  - G82 — Providing a text alternative that identifies the purpose of interactive non-text content
  - ARIA9 — Using aria-labelledby to concatenate a label from several text nodes
  - H24 — Providing text alternatives for the area elements of image maps
  - H30 — Providing link text that describes the purpose of a link for anchor elements
  - H36 — Using alt attributes on images used as submit buttons
  - H44 — Using label elements to associate text labels with form controls
  - H65 — Using the title attribute to identify form controls when the label element cannot be used
  - G68 — Providing a short text alternative that describes the purpose of live audio-only and live video-only content
  - G100 — Providing a short text alternative which is the accepted name or a descriptive name of the non-text content
  - G143 — Providing a text alternative that describes the purpose of the CAPTCHA
  - G144 — Ensuring that the web page contains another CAPTCHA serving the same purpose using a different modality
  - C9 — Using CSS to include decorative images
  - H67 — Using null alt text and no title attribute on img elements for images that assistive technology should ignore
  - PDF4 — Hiding decorative images with the Artifact tag in PDF documents
- **ACT test rules:** [Element marked as decorative is not exposed](https://www.w3.org/WAI/standards-guidelines/act/rules/46ca7f/); [Image accessible name is descriptive](https://www.w3.org/WAI/standards-guidelines/act/rules/qt1vmo/); [Image button has non-empty accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/59796f/); [Image has non-empty accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/23a2a8/); [Link has non-empty accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/c487ae/); [Object element rendering non-text content has non-empty accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/8fc3b6/); [SVG element with explicit role has non-empty accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/7d6734/); [Image filename is accessible name for image](https://www.w3.org/WAI/standards-guidelines/act/rules/9eb3f6/proposed/); [Image not in the accessibility tree is decorative](https://www.w3.org/WAI/standards-guidelines/act/rules/e88epe/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <img src="q3-sales.png" alt="Q3 sales rose 12% to $4.2M">
  <button aria-label="Close dialog">
    <svg aria-hidden="true" focusable="false">...</svg>
  </button>
  <img src="divider.png" alt="">
  ```

  Fail:

  ```html
  <img src="q3-sales.png">
  <button>
    <svg>...</svg>
  </button>
  <img src="divider.png" alt="decorative divider image">
  ```

## Guideline 1.2 — Time-based Media

> Provide alternatives for time-based media.

<a id="wcag-1-2-1"></a>
### WCAG-1.2.1 — Audio-only and Video-only (Prerecorded) (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#audio-only-and-video-only-prerecorded> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/audio-only-and-video-only-prerecorded.html>

- **Text:**

  > For prerecorded audio-only and prerecorded video-only media, the following are true, except when the audio or video is a media alternative for text and is clearly labeled as such:
  >
  > - **Prerecorded Audio-only:** An alternative for time-based media is provided that presents equivalent information for prerecorded audio-only content.
  > - **Prerecorded Video-only:** Either an alternative for time-based media or an audio track is provided that presents equivalent information for prerecorded video-only content.

- **Applies to:** prerecorded audio-only (podcasts, audio clips), prerecorded video-only (silent animations, screencasts without sound)
- **Testability:** manual — axe-core has only the deprecated audio-caption rule, which cannot confirm an equivalent exists. A static scanner can list `<audio>`/`<video>` elements and embedded players and look for an adjacent transcript link; a human must verify the alternative is complete and equivalent.
  - **axe-core rules (4.13.0):** `audio-caption(deprecated)`
- **Test procedure:**
  1. List all prerecorded audio-only and video-only media on the page.
  2. Check whether the media is itself a clearly labelled alternative for text (exempt).
  3. For audio-only, locate a transcript and compare it against the audio for completeness (speech, speaker ids, meaningful sounds).
  4. For video-only, locate a text alternative or an audio track and verify it conveys all visual information.
  5. Confirm the alternative is reachable from, or adjacent to, the media.
- **Common failures:**
  - F30 — Failure of Success Criterion 1.1.1 and 1.2.1 due to using text alternatives that are not alternatives (e.g., filenames or placeholder text)
  - F67 — Failure of Success Criterion 1.1.1 and 1.2.1 due to providing long descriptions for non-text content that does not serve the same purpose or does not present the same information
  - Pattern: Podcast `<audio controls src="ep1.mp3">` with no transcript anywhere on the page.
  - Pattern: Silent product demo `<video autoplay muted loop>` with no description or narration.
  - Pattern: Transcript that summarises instead of reproducing the audio content.
- **Sufficient techniques:**
  - G158 — Providing an alternative for time-based media for audio-only content
  - G159 — Providing an alternative for time-based media for video-only content
  - G166 — Providing audio that describes the important video content and describing it as such
- **ACT test rules:** [Audio and visuals of video element have transcript](https://www.w3.org/WAI/standards-guidelines/act/rules/1a02b0/proposed/); [Audio element content has text alternative](https://www.w3.org/WAI/standards-guidelines/act/rules/e7aa44/proposed/); [Video element auditory content has captions](https://www.w3.org/WAI/standards-guidelines/act/rules/f51b46/proposed/); [Video element visual-only content has accessible alternative](https://www.w3.org/WAI/standards-guidelines/act/rules/c3232f/proposed/); [Video element visual-only content has transcript](https://www.w3.org/WAI/standards-guidelines/act/rules/ee13b5/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <audio controls src="ep12.mp3"></audio>
  <a href="ep12-transcript.html">Episode 12 transcript</a>
  ```

  Fail:

  ```html
  <audio controls src="ep12.mp3"></audio>
  <!-- no transcript provided -->
  ```

<a id="wcag-1-2-2"></a>
### WCAG-1.2.2 — Captions (Prerecorded) (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#captions-prerecorded> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded.html>

- **Text:**

  > Captions are provided for all prerecorded audio content in synchronized media, except when the media is a media alternative for text and is clearly labeled as such.

- **Applies to:** prerecorded synchronized media (video with sound), embedded players (YouTube, Vimeo), custom video players
- **Testability:** manual — axe-core video-caption detects a `<video>` without a `<track kind="captions">` but cannot see burned-in captions or judge accuracy. A static scanner can flag `<video>` elements lacking a captions track; a page runner can check whether a captions track loads. Accuracy and synchronisation require human review.
  - **axe-core rules (4.13.0):** `video-caption`
- **Test procedure:**
  1. Find every prerecorded video that has an audio track.
  2. Turn on captions (closed or open) and confirm they are available for the whole duration.
  3. Spot-check accuracy: dialogue, speaker identification and meaningful non-speech sounds.
  4. Verify captions are synchronised with the audio.
  5. Treat auto-generated captions as failing unless they have been reviewed and corrected.
- **Common failures:**
  - F8 — Failure of Success Criterion 1.2.2 due to captions omitting some dialogue or important sound effects
  - F75 — Failure of Success Criterion 1.2.2 by providing synchronized media without captions when the synchronized media presents more information than is presented on the page
  - F74 — Failure of Success Criterion 1.2.2 and 1.2.8 due to not labeling a synchronized media alternative to text as an alternative
  - Pattern: `<video src="promo.mp4" controls>` with no `<track kind="captions">` and no open captions.
  - Pattern: Using `kind="subtitles"` that contain only dialogue translation and omit sound cues.
  - Pattern: Unedited auto-generated captions with frequent errors.
  - Pattern: Custom player that hides the captions toggle or fails to render `<track>` cues.
- **Sufficient techniques:**
  - G93 — Providing open (always visible) captions
  - G87 — Providing closed captions
  - SM11 — Providing captions through synchronized text streams in SMIL 1.0
  - SM12 — Providing captions through synchronized text streams in SMIL 2.0
  - H95 — Using the track element to provide captions
- **ACT test rules:** [Video element auditory content has accessible alternative](https://www.w3.org/WAI/standards-guidelines/act/rules/eac66b/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <video controls src="launch.mp4">
    <track kind="captions" src="launch.en.vtt" srclang="en" label="English" default>
  </video>
  ```

  Fail:

  ```html
  <video controls src="launch.mp4"></video>
  ```

<a id="wcag-1-2-3"></a>
### WCAG-1.2.3 — Audio Description or Media Alternative (Prerecorded) (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#audio-description-or-media-alternative-prerecorded> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/audio-description-or-media-alternative-prerecorded.html>

- **Text:**

  > An alternative for time-based media or audio description of the prerecorded video content is provided for synchronized media, except when the media is a media alternative for text and is clearly labeled as such.

- **Applies to:** prerecorded synchronized media with visual information not conveyed by the soundtrack
- **Testability:** manual — No axe-core rule applies. A static scanner can list videos lacking a `<track kind="descriptions">` or an adjacent transcript link as candidates; a human must judge whether visual information is conveyed.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Watch each prerecorded video with sound and note visual information not conveyed by the audio.
  2. Check for an audio-described version or a description track.
  3. Alternatively, check for a full text alternative (transcript including visual descriptions).
  4. Confirm the chosen alternative covers all important visual content.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Tutorial video where on-screen steps are shown but never spoken, with no description or transcript.
  - Pattern: Transcript that only reproduces dialogue and omits on-screen text and actions.
  - Pattern: `<track kind="descriptions">` file that is empty or covers only part of the video.
- **Sufficient techniques:**
  - G69 — Providing an alternative for time based media
  - G58 — Placing a link to the alternative for time-based media immediately next to the non-text content
  - H53 — Using the body of the object element
  - G78 — Providing a second, user-selectable, audio track that includes audio descriptions
  - G173 — Providing a version of a movie with audio descriptions
  - SM6 — Providing audio description in SMIL 1.0
  - SM7 — Providing audio description in SMIL 2.0
  - G226 — Providing audio descriptions by incorporating narration in the soundtrack
  - G8 — Providing a movie with extended audio descriptions
  - SM1 — Adding extended audio description in SMIL 1.0
  - SM2 — Adding extended audio description in SMIL 2.0
  - G203 — Using a static text alternative to describe a talking head video
- **ACT test rules:** [Video element visual content has accessible alternative](https://www.w3.org/WAI/standards-guidelines/act/rules/c5a4ea/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <video controls src="setup.mp4">
    <track kind="captions" src="setup.vtt" srclang="en">
  </video>
  <a href="setup-transcript.html">Full transcript with visual descriptions</a>
  ```

  Fail:

  ```html
  <video controls src="setup.mp4">
    <track kind="captions" src="setup.vtt" srclang="en">
  </video>
  <!-- visual steps are never described -->
  ```

<a id="wcag-1-2-4"></a>
### WCAG-1.2.4 — Captions (Live) (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#captions-live> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/captions-live.html>

- **Text:**

  > Captions are provided for all live audio content in synchronized media.

- **Applies to:** live synchronized media: webcasts, live streams, live events, live video conferences published as content
- **Testability:** manual — No automated rule applies. A page runner can confirm the player exposes a captions control; a human must verify real-time captions are present and reasonably accurate during a live session.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify live audio-visual streams on the page.
  2. During a live broadcast (or a test stream), enable captions.
  3. Confirm captions appear for the spoken content with acceptable delay and accuracy.
  4. Confirm the captions control is operable and discoverable.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Live stream embed with no CART or real-time caption feed.
  - Pattern: Captions available only in a later on-demand recording, not during the live event.
- **Sufficient techniques:**
  - G9 — Creating captions for live synchronized media
  - G93 — Providing open (always visible) captions
  - G87 — Providing closed captions
  - SM11 — Providing captions through synchronized text streams in SMIL 1.0
  - SM12 — Providing captions through synchronized text streams in SMIL 2.0
- **Pass/fail example:**

  Pass:

  ```html
  <div class="live-player" data-stream="keynote">
    <!-- stream includes a CART caption feed rendered as a captions track -->
    <button aria-pressed="true">Captions</button>
  </div>
  ```

  Fail:

  ```html
  <div class="live-player" data-stream="keynote">
    <!-- no caption feed; captions button absent -->
  </div>
  ```

<a id="wcag-1-2-5"></a>
### WCAG-1.2.5 — Audio Description (Prerecorded) (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#audio-description-prerecorded> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/audio-description-prerecorded.html>

- **Text:**

  > Audio description is provided for all prerecorded video content in synchronized media.

- **Applies to:** prerecorded synchronized media with visual information not in the soundtrack
- **Testability:** manual — No axe-core rule applies. A static scanner can flag `<video>` without `<track kind="descriptions">` or a link to a described version; a human must judge whether description is needed and adequate.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Watch each prerecorded video and identify visual content not conveyed by the audio.
  2. Check for audio description: a described version, a description track, or narration that already covers visual content (integrated description).
  3. Confirm descriptions fit into natural pauses and cover all important visual information.
  4. Note: a text transcript alone does not satisfy this AA criterion.
- **Common failures:**
  - F113 — Failure of Success Criterion 1.2.5 due to not using available pauses in dialogue to provide audio descriptions of important visual content
  - Pattern: Offering only a text transcript for a video whose visuals are not narrated.
  - Pattern: Description track that exists but is never exposed by the custom player.
  - Pattern: Silent on-screen captions of key info (prices, names) that are never spoken.
- **Sufficient techniques:**
  - G78 — Providing a second, user-selectable, audio track that includes audio descriptions
  - G173 — Providing a version of a movie with audio descriptions
  - SM6 — Providing audio description in SMIL 1.0
  - SM7 — Providing audio description in SMIL 2.0
  - G226 — Providing audio descriptions by incorporating narration in the soundtrack
  - G8 — Providing a movie with extended audio descriptions
  - SM1 — Adding extended audio description in SMIL 1.0
  - SM2 — Adding extended audio description in SMIL 2.0
  - G203 — Using a static text alternative to describe a talking head video
- **ACT test rules:** [Video element visual content has accessible alternative](https://www.w3.org/WAI/standards-guidelines/act/rules/c5a4ea/proposed/); [Video element visual content has strict accessible alternative](https://www.w3.org/WAI/standards-guidelines/act/rules/1ec09b/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <video controls src="tour.mp4">
    <track kind="captions" src="tour.vtt" srclang="en">
  </video>
  <a href="tour-described.mp4">Audio-described version</a>
  ```

  Fail:

  ```html
  <video controls src="tour.mp4">
    <track kind="captions" src="tour.vtt" srclang="en">
  </video>
  <!-- visuals not narrated, no described version -->
  ```

<a id="wcag-1-2-6"></a>
### WCAG-1.2.6 — Sign Language (Prerecorded) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#sign-language-prerecorded> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/sign-language-prerecorded.html>

- **Text:**

  > Sign language interpretation is provided for all prerecorded audio content in synchronized media.

- **Applies to:** prerecorded synchronized media with audio
- **Testability:** manual — No automated rule applies. A human must confirm a sign-language interpretation is provided (inset or alternate version) and is complete.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify prerecorded videos with audio content.
  2. Check for sign-language interpretation embedded in the video or a linked alternate version.
  3. Confirm the interpreter is visible, large enough, and covers all audio content.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Captions provided but no sign-language version for key video content.
  - Pattern: Interpreter window too small or cropped by player controls.
- **Sufficient techniques:**
  - G54 — Including a sign language interpreter in the video stream
  - G81 — Providing a synchronized video of the sign language interpreter that can be displayed in a different viewport or overlaid on the image by the player
  - SM13 — Providing sign language interpretation through synchronized video streams in SMIL 1.0
  - SM14 — Providing sign language interpretation through synchronized video streams in SMIL 2.0
- **Pass/fail example:**

  Pass:

  ```html
  <video controls src="welcome.mp4"></video>
  <a href="welcome-asl.mp4">Watch with ASL interpretation</a>
  ```

  Fail:

  ```html
  <video controls src="welcome.mp4"></video>
  <!-- no sign language version -->
  ```

<a id="wcag-1-2-7"></a>
### WCAG-1.2.7 — Extended Audio Description (Prerecorded) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#extended-audio-description-prerecorded> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/extended-audio-description-prerecorded.html>

- **Text:**

  > Where pauses in foreground audio are insufficient to allow audio descriptions to convey the sense of the video, extended audio description is provided for all prerecorded video content in synchronized media.

- **Applies to:** prerecorded synchronized media where natural pauses are too short for standard audio description
- **Testability:** manual — No automated rule applies. A human must review whether standard description is insufficient and, if so, whether an extended-description version (video pauses for description) exists.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify videos where needed descriptions do not fit into existing pauses.
  2. Check for an extended audio-described version that pauses the video to insert description.
  3. Confirm all important visual information is described.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Fast-paced video with standard description that omits visual details for lack of pause time.
  - Pattern: No option to pause playback for extended description.
- **Sufficient techniques:**
  - G8 — Providing a movie with extended audio descriptions
  - SM1 — Adding extended audio description in SMIL 1.0
  - SM2 — Adding extended audio description in SMIL 2.0
- **Pass/fail example:**

  Pass:

  ```html
  <video controls src="lab.mp4"></video>
  <a href="lab-extended-ad.mp4">Version with extended audio description</a>
  ```

  Fail:

  ```html
  <video controls src="lab.mp4"></video>
  <!-- dense visuals, description truncated to fit gaps -->
  ```

<a id="wcag-1-2-8"></a>
### WCAG-1.2.8 — Media Alternative (Prerecorded) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#media-alternative-prerecorded> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/media-alternative-prerecorded.html>

- **Text:**

  > An alternative for time-based media is provided for all prerecorded synchronized media and for all prerecorded video-only media.

- **Applies to:** prerecorded synchronized media, prerecorded video-only media
- **Testability:** manual — No automated rule applies. A static scanner can check for a transcript link near media; a human must verify the alternative is a full, correctly ordered text version of both audio and visual information.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. For each prerecorded video, locate a full text alternative (descriptive transcript).
  2. Compare it with the video: dialogue, speaker identification, sounds, and all visual information.
  3. Confirm it is linked from or adjacent to the media.
- **Common failures:**
  - F74 — Failure of Success Criterion 1.2.2 and 1.2.8 due to not labeling a synchronized media alternative to text as an alternative
  - Pattern: Transcript that contains dialogue only, without visual descriptions.
  - Pattern: Alternative that is a marketing summary rather than a full equivalent.
- **Sufficient techniques:**
  - G69 — Providing an alternative for time based media
  - G58 — Placing a link to the alternative for time-based media immediately next to the non-text content
  - H53 — Using the body of the object element
  - G159 — Providing an alternative for time-based media for video-only content
- **ACT test rules:** [Audio and visuals of video element have transcript](https://www.w3.org/WAI/standards-guidelines/act/rules/1a02b0/proposed/); [Video element visual content has accessible alternative](https://www.w3.org/WAI/standards-guidelines/act/rules/c5a4ea/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <video controls src="demo.mp4"></video>
  <details>
    <summary>Descriptive transcript</summary>
    <p>[Screen shows the login page.] Narrator: "Enter your email..."</p>
  </details>
  ```

  Fail:

  ```html
  <video controls src="demo.mp4"></video>
  <p>This video shows how to log in.</p>
  ```

<a id="wcag-1-2-9"></a>
### WCAG-1.2.9 — Audio-only (Live) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#audio-only-live> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/audio-only-live.html>

- **Text:**

  > An alternative for time-based media that presents equivalent information for live audio-only content is provided.

- **Applies to:** live audio-only content: radio streams, live audio webcasts
- **Testability:** manual — No automated rule applies. A human must verify during a live session that a real-time text alternative (e.g. live captioning or a live text stream) is provided.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify live audio-only streams.
  2. During a live session, locate the real-time text alternative.
  3. Confirm it conveys the spoken content and meaningful sounds with acceptable delay.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Live radio stream with no real-time text feed.
  - Pattern: Text published only after the event ends.
- **Sufficient techniques:**
  - G151 — Providing a link to a text transcript of a prepared statement or script if the script is followed
  - G150 — Providing text based alternatives for live audio-only content
  - G157 — Incorporating a live audio captioning service into a web page
- **Pass/fail example:**

  Pass:

  ```html
  <audio controls src="live-stream"></audio>
  <div role="log" aria-live="polite" id="live-text"><!-- live CART text --></div>
  ```

  Fail:

  ```html
  <audio controls src="live-stream"></audio>
  ```

## Guideline 1.3 — Adaptable

> Create content that can be presented in different ways (for example simpler layout) without losing information or structure.

<a id="wcag-1-3-1"></a>
### WCAG-1.3.1 — Info and Relationships (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#info-and-relationships> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html>

- **Text:**

  > Information, structure, and relationships conveyed through presentation can be programmatically determined or are available in text.

- **Applies to:** headings, lists, tables, forms and labels, landmarks/regions, emphasis, grouped controls, ARIA widgets
- **Testability:** assisted — axe-core (list, listitem, definition-list, dlitem, td-headers-attr, th-has-data-cells, aria-required-children, aria-required-parent, aria-hidden-body; experimental p-as-heading, td-has-header, table-fake-caption) finds structural errors but not missing structure that is only visual. A static scanner can flag styled `<div>`/`<b>` used as headings, layout tables with `<th>`, and inputs without associated labels; a page runner can compare visual heading candidates (large/bold text) with the heading tree. Human review confirms structure matches visual presentation.
  - **axe-core rules (4.13.0):** `aria-hidden-body`, `aria-required-children`, `aria-required-parent`, `definition-list`, `dlitem`, `list`, `listitem`, `p-as-heading(experimental)`, `table-fake-caption(experimental)`, `td-has-header(experimental)`, `td-headers-attr`, `th-has-data-cells`
- **Test procedure:**
  1. Compare the visual structure (headings, lists, tables, groups, required markers) with the accessibility tree.
  2. Check headings use `<h1>`–`<h6>` or `role="heading"` with a level matching the visual hierarchy.
  3. Check data tables use `<th>`, `scope` or `headers`, and captions where needed; layout tables have no header semantics.
  4. Check each form field has a programmatic label and related fields are grouped (`<fieldset>`/`<legend>` or `role="group"`).
  5. Check information conveyed by styling (bold, color, position) is also available in text or markup.
- **Common failures:**
  - F2 — Failure of Success Criterion 1.3.1 due to using changes in text presentation to convey information without using the appropriate markup or text
  - F33 — Failure of Success Criterion 1.3.1 and 1.3.2 due to using white space characters to create multiple columns in plain text content
  - F34 — Failure of Success Criterion 1.3.1 and 1.3.2 due to using white space characters to format tables in plain text content
  - F42 — Failure of Success Criteria 1.3.1, 2.1.1, 2.1.3, or 4.1.2 when emulating links
  - F43 — Failure of Success Criterion 1.3.1 due to using structural markup in a way that does not represent relationships in the content
  - F46 — Failure of Success Criterion 1.3.1 due to using th elements, … layout tables
  - F48 — Failure of Success Criterion 1.3.1 due to using the pre element to markup tabular information
  - F90 — Failure of Success Criterion 1.3.1 for incorrectly associating table headers and content via the headers and id attributes
  - F91 — Failure of Success Criterion 1.3.1 for not correctly marking up table headers
  - F92 — Failure of Success Criterion 1.3.1 due to the use of role presentation on content which conveys semantic information
  - F111 — Failure of Success Criteria 1.3.1, 2.5.3, and 4.1.2 due to a control with visible label text but no accessible name
  - Pattern: Visual heading built with `<div class="h2">` or `<p><b>` instead of a heading element.
  - Pattern: Label text next to an input without `<label for>` or `aria-labelledby`.
  - Pattern: Data table built from `<div>` grids with no `role="table"`/`row`/`cell` or header association.
  - Pattern: Radio group with no `<fieldset>`/`<legend>` so the question is not announced.
  - Pattern: List items rendered as `<div>`s with bullet characters.
- **Sufficient techniques:**
  - ARIA11 — Using ARIA landmarks to identify regions of a page
  - H101 — Using semantic HTML elements to identify regions of a page
  - ARIA12 — Using role=heading to identify headings
  - ARIA13 — Using aria-labelledby to name regions and landmarks
  - ARIA16 — Using aria-labelledby to provide a name for user interface controls
  - ARIA17 — Using grouping roles to identify related form controls
  - ARIA20 — Using the region role to identify a region of the page
  - G115 — Using semantic elements to mark up structure
  - H49 — Using semantic markup to mark emphasized or special text
  - G117 — Using text to convey information that is conveyed by variations in presentation of text
  - G140 — Separating information and structure from presentation to enable different presentations
  - ARIA24 — Semantically identifying a font icon with role="img"
  - ARIA26 — Using aria-current to identify the current item in a set
  - G138 — Using semantic markup whenever color cues are used
  - H51 — Using table markup to present tabular information
  - PDF6 — Using table elements for table markup in PDF Documents
  - PDF20 — Using Adobe Acrobat Pro's Table Editor to repair mistagged tables
  - H39 — Using caption elements to associate data table captions with data tables
  - H63 — Using the scope attribute to associate header cells with data cells in data tables
  - H43 — Using id and headers attributes to associate data cells with header cells in data tables
  - H44 — Using label elements to associate text labels with form controls
  - H65 — Using the title attribute to identify form controls when the label element cannot be used
  - PDF10 — Providing labels for interactive form controls in PDF documents
  - PDF12 — Providing name, role, value information for form fields in PDF documents
  - H71 — Providing a description for groups of form controls using fieldset and legend elements
  - H85 — Using optgroup to group option elements inside a select
  - H48 — Using ol, ul and dl for lists or groups of links
  - H42 — Using h1-h6 to identify headings
  - PDF9 — Providing headings by marking content with heading tags in PDF documents
  - PDF11 — Providing links and link text using the Link annotation and the /Link structure element in PDF documents
  - PDF17 — Specifying consistent page numbering for PDF documents
  - PDF21 — Using List tags for lists in PDF documents
  - H97 — Grouping related links using the nav element
  - T1 — Using standard text formatting conventions for paragraphs
  - T2 — Using standard text formatting conventions for lists
  - T3 — Using standard text formatting conventions for headings
- **ACT test rules:** [ARIA attribute is defined in WAI-ARIA](https://www.w3.org/WAI/standards-guidelines/act/rules/5f99a7/); [ARIA state or property has valid value](https://www.w3.org/WAI/standards-guidelines/act/rules/6a7281/); [Element with role attribute has required states and properties](https://www.w3.org/WAI/standards-guidelines/act/rules/4e8ab6/); [Form field has non-empty accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/e086e5/); [Headers attribute specified on a cell refers to cells in the same table element](https://www.w3.org/WAI/standards-guidelines/act/rules/a25f45/); [Role attribute has valid value](https://www.w3.org/WAI/standards-guidelines/act/rules/674b10/); [ARIA global properties not used where prohibited](https://www.w3.org/WAI/standards-guidelines/act/rules/kb1m8s/proposed/); [ARIA required context role](https://www.w3.org/WAI/standards-guidelines/act/rules/ff89c9/proposed/); [ARIA required ID references exist](https://www.w3.org/WAI/standards-guidelines/act/rules/in6db8/proposed/); [ARIA required owned elements](https://www.w3.org/WAI/standards-guidelines/act/rules/bc4a75/proposed/); [ARIA state or property is permitted](https://www.w3.org/WAI/standards-guidelines/act/rules/5c01ea/proposed/); [Audio and visuals of video element have transcript](https://www.w3.org/WAI/standards-guidelines/act/rules/1a02b0/proposed/); [Table header cell has assigned cells](https://www.w3.org/WAI/standards-guidelines/act/rules/d0f69e/proposed/); [Video element visual-only content has transcript](https://www.w3.org/WAI/standards-guidelines/act/rules/ee13b5/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <h2>Shipping</h2>
  <fieldset>
    <legend>Delivery speed</legend>
    <label><input type="radio" name="s" value="std"> Standard</label>
    <label><input type="radio" name="s" value="exp"> Express</label>
  </fieldset>
  ```

  Fail:

  ```html
  <div class="heading-lg">Shipping</div>
  <p>Delivery speed</p>
  <input type="radio" name="s" value="std"> Standard
  <input type="radio" name="s" value="exp"> Express
  ```

<a id="wcag-1-3-2"></a>
### WCAG-1.3.2 — Meaningful Sequence (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#meaningful-sequence> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/meaningful-sequence.html>

- **Text:**

  > When the sequence in which content is presented affects its meaning, a correct reading sequence can be programmatically determined.

- **Applies to:** reading order of page content, CSS layouts (flex/grid order, absolute positioning), multi-column text, tables used for layout
- **Testability:** manual — No axe-core rule directly tests this. A static scanner can flag CSS `order`, `flex-direction: *-reverse`, `grid-area` placement and absolute positioning as candidates; a page runner can compare DOM order with visual (bounding-box) order. A human decides whether a mismatch changes meaning.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Disable CSS or linearise the page (or use a screen reader) and read content in DOM order.
  2. Compare with the visual reading order.
  3. Where order differs, judge whether meaning or understanding is affected.
  4. Check that whitespace characters are not used to create visual columns within words or tables.
- **Common failures:**
  - F34 — Failure of Success Criterion 1.3.1 and 1.3.2 due to using white space characters to format tables in plain text content
  - F33 — Failure of Success Criterion 1.3.1 and 1.3.2 due to using white space characters to create multiple columns in plain text content
  - F32 — Failure of Success Criterion 1.3.2 due to using white space characters to control spacing within a word
  - F49 — Failure of Success Criterion 1.3.2 due to using an HTML layout table that does not make sense when linearized
  - F1 — Failure of Success Criterion 1.3.2 due to changing the meaning of content by positioning information with CSS
  - Pattern: CSS `order` or `flex-direction: row-reverse` placing the step-2 panel before step 1 in DOM.
  - Pattern: Absolutely positioned price label that appears after the product it describes in DOM.
  - Pattern: Using spaces or `&nbsp;` to lay out a table or spell words with gaps.
- **Sufficient techniques:**
  - G57 — Ordering the content in a meaningful sequence
  - H34 — Using a Unicode right-to-left mark (RLM) or left-to-right mark (LRM) to mix text direction inline
  - H56 — Using the dir attribute on an inline element to resolve problems with nested directional runs
  - C6 — Positioning content based on structural markup
  - C8 — Using CSS letter-spacing to control spacing within a word
  - C27 — Making the DOM order match the visual order
  - PDF3 — Ensuring correct tab and reading order in PDF documents
- **Pass/fail example:**

  Pass:

  ```html
  <ol class="steps">
    <li>Choose plan</li>
    <li>Enter details</li>
    <li>Pay</li>
  </ol>
  ```

  Fail:

  ```html
  <div style="display:flex;flex-direction:row-reverse">
    <div>Pay</div><div>Enter details</div><div>Choose plan</div>
  </div>
  ```

<a id="wcag-1-3-3"></a>
### WCAG-1.3.3 — Sensory Characteristics (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#sensory-characteristics> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/sensory-characteristics.html>

- **Text:**

  > Instructions provided for understanding and operating content do not rely solely on sensory characteristics of components such as shape, color, size, visual location, orientation, or sound.
  >
  > *Note:* For requirements related to color, refer to Guideline 1.4.

- **Applies to:** instructions, error messages, help text referencing shape, size, visual location, orientation, or sound
- **Testability:** manual — No automated rule applies. A static scanner can grep text for phrases like "click the round button", "on the right", "in red", "after the beep" as candidates; a human confirms whether a non-sensory cue is also present.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Find instructions that tell users how to operate or understand content.
  2. Identify references relying solely on shape, color, size, visual location, orientation or sound.
  3. Confirm each such instruction also includes a non-sensory identifier (label text, name).
- **Common failures:**
  - F14 — Failure of Success Criterion 1.3.3 due to identifying content only by its shape or location
  - F26 — Failure of Success Criterion 1.3.3 due to using a graphical symbol alone to convey information
  - Pattern: "Press the green button on the right to continue" where the button has no mentioned text label.
  - Pattern: "Required fields are shown with a star icon" referencing only an unlabeled icon.
  - Pattern: "Wait for the beep, then speak" with no visual or text cue.
- **Sufficient techniques:**
  - G96 — Providing textual identification of items that otherwise rely only on sensory information to be understood
- **ACT test rules:** [Content has alternative for visual reference](https://www.w3.org/WAI/standards-guidelines/act/rules/9bd38c/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <p>Select <strong>Continue</strong> (the round button at the bottom right) to proceed.</p>
  ```

  Fail:

  ```html
  <p>Select the round button at the bottom right to proceed.</p>
  ```

<a id="wcag-1-3-4"></a>
### WCAG-1.3.4 — Orientation (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#orientation> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/orientation.html>

- **Text:**

  > Content does not restrict its view and operation to a single display orientation, such as portrait or landscape, unless a specific display orientation is essential.
  >
  > *Note:* Examples where a particular display orientation may be essential are a bank check, a piano application, slides for a projector or television, or virtual reality content where content is not necessarily restricted to landscape or portrait display orientation.

- **Applies to:** page layout, CSS media queries, JavaScript orientation locks, mobile web apps
- **Testability:** assisted — axe-core has the experimental css-orientation-lock rule for CSS transforms tied to orientation media queries. A static scanner can flag `screen.orientation.lock()` and `@media (orientation: ...)` rules that hide content; a page runner can render in portrait and landscape viewports and compare content. A human confirms whether a lock is essential.
  - **axe-core rules (4.13.0):** `css-orientation-lock(experimental)`
- **Test procedure:**
  1. Load the page on a device or emulator in portrait, then landscape.
  2. Confirm content and functionality are available in both orientations without rotating the device.
  3. Look for messages like "rotate your device" or content hidden in one orientation.
  4. If locked, judge whether orientation is essential (e.g. piano app, bank check).
- **Common failures:**
  - F97 — Failure due to locking the orientation to landscape or portrait view
  - F100 — Failure of Success Criterion 1.3.4 due to showing a message asking to reorient device
  - Pattern: `@media (orientation: portrait) { body { display: none } }` with a "rotate your device" overlay.
  - Pattern: `screen.orientation.lock('landscape')` in a web app without an essential need.
  - Pattern: CSS `transform: rotate(90deg)` on the root in one orientation to force the layout.
- **Sufficient techniques:**
  - G214 — Using a control to allow access to content in different orientations which is otherwise restricted
- **ACT test rules:** [Orientation of the page is not restricted using CSS transforms](https://www.w3.org/WAI/standards-guidelines/act/rules/b33eff/)
- **Pass/fail example:**

  Pass:

  ```css
  @media (orientation: landscape) {
    .layout { grid-template-columns: 1fr 2fr; }
  }
  /* both orientations show all content */
  ```

  Fail:

  ```css
  @media (orientation: portrait) {
    main { display: none; }
    .rotate-msg { display: block; }
  }
  ```

<a id="wcag-1-3-5"></a>
### WCAG-1.3.5 — Identify Input Purpose (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#identify-input-purpose> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/identify-input-purpose.html>

- **Text:**

  > The purpose of each input field collecting information about the user can be programmatically determined when:
  >
  > - The input field serves a purpose identified in the Input Purposes for user interface components section; and
  > - The content is implemented using technologies with support for identifying the expected meaning for form input data.

- **Applies to:** form inputs collecting user information (name, email, address, phone, payment, username, password)
- **Testability:** assisted — axe-core autocomplete-valid validates `autocomplete` values that are present but cannot know which fields collect user data. A static scanner can flag inputs whose name/label suggest personal data (email, tel, address) but lack `autocomplete`; a human confirms the field purpose and the correct token.
  - **axe-core rules (4.13.0):** `autocomplete-valid`
- **Test procedure:**
  1. Identify form fields that collect information about the user themselves.
  2. Map each field to the matching token from the HTML autofill list (e.g. `email`, `given-name`, `tel`, `street-address`).
  3. Check the field has the correct `autocomplete` value.
  4. Confirm fields about other people (e.g. a gift recipient) are not required to use personal tokens.
- **Common failures:**
  - F107 — Failure of Success Criterion 1.3.5 due to incorrect autocomplete attribute values
  - Pattern: `<input type="email" name="email">` with no `autocomplete` attribute.
  - Pattern: `autocomplete="off"` on the user's own name or address fields.
  - Pattern: Invalid or misspelled tokens such as `autocomplete="phone"` instead of `tel`.
- **Sufficient techniques:**
  - H98 — Using HTML autocomplete attributes
- **ACT test rules:** [Autocomplete attribute has valid value](https://www.w3.org/WAI/standards-guidelines/act/rules/73f2c2/)
- **Pass/fail example:**

  Pass:

  ```html
  <label for="em">Email</label>
  <input id="em" type="email" autocomplete="email">
  <label for="fn">First name</label>
  <input id="fn" autocomplete="given-name">
  ```

  Fail:

  ```html
  <label for="em">Email</label>
  <input id="em" type="email" autocomplete="off">
  <label for="fn">First name</label>
  <input id="fn" autocomplete="firstname">
  ```

<a id="wcag-1-3-6"></a>
### WCAG-1.3.6 — Identify Purpose (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#identify-purpose> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/identify-purpose.html>

- **Text:**

  > In content implemented using markup languages, the purpose of user interface components, icons, and regions can be programmatically determined.

- **Applies to:** UI components, icons, regions/landmarks, symbols conveying purpose
- **Testability:** manual — No axe-core rule maps to this SC (landmark rules are best-practice). A static scanner can list landmarks and icon-only controls; a human judges whether component, icon and region purposes are programmatically identifiable (landmarks, ARIA, `autocomplete`, personalisation metadata).
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Check page regions use landmark elements or roles (`header`, `nav`, `main`, `footer`, `aside`, `search`).
  2. Check common icons and controls expose their purpose via accessible names or metadata.
  3. Check input fields about the user expose purpose (overlaps 1.3.5).
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Page built entirely with `<div>` wrappers and no landmarks.
  - Pattern: Icon-only navigation with no programmatic purpose beyond an image.
- **Sufficient techniques:**
  - ARIA11 — Using ARIA landmarks to identify regions of a page
- **Pass/fail example:**

  Pass:

  ```html
  <header>...</header>
  <nav aria-label="Primary">...</nav>
  <main>...</main>
  <footer>...</footer>
  ```

  Fail:

  ```html
  <div class="top">...</div>
  <div class="menu">...</div>
  <div class="content">...</div>
  ```

## Guideline 1.4 — Distinguishable

> Make it easier for users to see and hear content including separating foreground from background.

<a id="wcag-1-4-1"></a>
### WCAG-1.4.1 — Use of Color (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#use-of-color> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html>

- **Text:**

  > Color is not used as the only visual means of conveying information, indicating an action, prompting a response, or distinguishing a visual element.
  >
  > *Note:* This success criterion addresses color perception specifically. Other forms of perception are covered in Guideline 1.3 including programmatic access to color and other visual presentation coding.

- **Applies to:** links within text, form validation states, charts and graphs, status indicators, required-field markers
- **Testability:** assisted — axe-core link-in-text-block flags inline links distinguished only by color with insufficient contrast to surrounding text. A static scanner can flag CSS `text-decoration: none` on inline links and error styles that only change `color`/`border-color`; a page runner can render in grayscale for review. Charts and state indicators need human review.
  - **axe-core rules (4.13.0):** `link-in-text-block`
- **Test procedure:**
  1. Identify information conveyed by color: links, errors, required fields, chart series, status badges.
  2. View the page in grayscale (or simulate color blindness) and check the information is still available.
  3. For inline links distinguished only by color, check 3:1 contrast with surrounding text plus a non-color cue on focus/hover, or a non-color cue by default.
  4. Confirm a text, icon, pattern or underline accompanies the color cue.
- **Common failures:**
  - F13 — Failure of Success Criterion 1.1.1 and 1.4.1 due to having a text alternative that does not include information that is conveyed by color differences in the image
  - F73 — Failure of Success Criterion 1.4.1 due to creating links that are not visually evident without color vision
  - F81 — Failure of Success Criterion 1.4.1 due to identifying required or error fields using color differences only
  - Pattern: `a { text-decoration: none; color: #0055aa }` inside paragraphs with no underline.
  - Pattern: Invalid inputs indicated only by `border-color: red`.
  - Pattern: Line chart where series differ only by stroke color with no labels or patterns.
  - Pattern: "Fields in red are required" with no asterisk or text.
- **Sufficient techniques:**
  - G14 — Ensuring that information conveyed by color differences is also available in text
  - G205 — Including a text cue for colored form control labels
  - G182 — Ensuring that additional visual cues are available when text color differences are used to convey information
  - G183 — Using a contrast ratio of at least 3:1 to distinguish inline text links from surrounding text
  - G111 — Using color and pattern
- **Pass/fail example:**

  Pass:

  ```css
  p a { color: #0055aa; text-decoration: underline; }
  .field--error { border-color: #b00020; }
  .field--error::before { content: "Error: "; }
  ```

  Fail:

  ```css
  p a { color: #0055aa; text-decoration: none; }
  .field--error { border-color: #b00020; }
  ```

<a id="wcag-1-4-2"></a>
### WCAG-1.4.2 — Audio Control (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#audio-control> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/audio-control.html>

- **Text:**

  > If any audio on a web page plays automatically for more than 3 seconds, either a mechanism is available to pause or stop the audio, or a mechanism is available to control audio volume independently from the overall system volume level.
  >
  > *Note:* Since any content that does not meet this success criterion can interfere with a user's ability to use the whole page, all content on the web page (whether or not it is used to meet other success criteria) must meet this success criterion. See Conformance Requirement 5: Non-Interference.

- **Applies to:** autoplaying audio, background music, videos with sound that start automatically
- **Testability:** assisted — axe-core no-autoplay-audio flags `<audio>`/`<video>` with `autoplay` that plays sound over 3 seconds without controls. A static scanner can flag `autoplay` attributes and `.play()` on load; a page runner can detect media playing after load. Human confirms a pause/stop or independent volume control exists.
  - **axe-core rules (4.13.0):** `no-autoplay-audio`
- **Test procedure:**
  1. Load the page and listen for audio that starts without user action.
  2. If it plays more than 3 seconds, find a mechanism to pause/stop it or control its volume independently of system volume.
  3. Confirm the mechanism is near the start of the page and keyboard operable.
- **Common failures:**
  - F23 — Failure of 1.4.2 due to playing a sound longer than 3 seconds where there is no mechanism to turn it off
  - F93 — Failure of Success Criterion 1.4.2 for absence of a way to pause or stop an HTML5 media element that autoplays
  - Pattern: `<video autoplay src="hero.mp4">` with sound and no controls.
  - Pattern: `new Audio('bg.mp3').play()` on page load with no stop control.
  - Pattern: Mute control placed at the bottom of a long page.
- **Sufficient techniques:**
  - G60 — Playing a sound that turns off automatically within three seconds
  - G170 — Providing a control near the beginning of the web page that turns off sounds that play automatically
  - G171 — Playing sounds only on user request
- **ACT test rules:** [Audio or video element avoids automatically playing audio](https://www.w3.org/WAI/standards-guidelines/act/rules/80f0bf/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <video autoplay muted loop playsinline src="hero.mp4"></video>
  ```

  Fail:

  ```html
  <audio autoplay loop src="background-music.mp3"></audio>
  ```

<a id="wcag-1-4-3"></a>
### WCAG-1.4.3 — Contrast (Minimum) (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#contrast-minimum> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html>

- **Text:**

  > The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for the following:
  >
  > - **Large Text:** Large-scale text and images of large-scale text have a contrast ratio of at least 3:1;
  > - **Incidental:** Text or images of text that are part of an inactive user interface component, that are pure decoration, that are not visible to anyone, or that are part of a picture that contains significant other visual content, have no contrast requirement.
  > - **Logotypes:** Text that is part of a logo or brand name has no contrast requirement.

- **Applies to:** text, images of text, placeholder text, text over images and gradients, link and button text
- **Testability:** automated — axe-core color-contrast computes ratios for most text but returns needs-review for text over images, gradients, or pseudo-elements. A static scanner can compute contrast for literal CSS color pairs; a page runner can sample rendered pixels behind text. Human review covers images of text and incomplete results.
  - **axe-core rules (4.13.0):** `color-contrast`
- **Test procedure:**
  1. Run an automated contrast check across page states (hover, focus, error, disabled excluded).
  2. For flagged or incomplete items, measure foreground and background colors with a contrast analyser.
  3. Apply thresholds: 4.5:1 for normal text, 3:1 for large text (≥24px or ≥18.66px bold).
  4. Check text over images/gradients at the lowest-contrast point.
  5. Exempt disabled components, pure decoration, incidental text and logos.
- **Common failures:**
  - F24 — Failure of Success Criterion 1.4.3, 1.4.6 and 1.4.8 due to specifying foreground colors without specifying background colors or vice versa
  - F83 — Failure of Success Criterion 1.4.3 and 1.4.6 due to using background images that do not provide sufficient contrast with foreground text (or images of text)
  - Pattern: Light gray text such as `color: #999` on white (2.8:1).
  - Pattern: Placeholder text used as the only visible hint with low contrast.
  - Pattern: White text over a photo hero without an overlay or text shadow.
  - Pattern: Brand-colored button `background: #f90; color: #fff` (about 2.1:1).
- **Sufficient techniques:**
  - G18 — Ensuring that a contrast ratio of at least 4.5:1 exists between text (and images of text) and background behind the text
  - G148 — Not specifying background color, not specifying text color, and not using technology features that change those defaults
  - G174 — Providing a control with a sufficient contrast ratio that allows users to switch to a presentation that uses sufficient contrast
  - G145 — Ensuring that a contrast ratio of at least 3:1 exists between text (and images of text) and background behind the text
- **ACT test rules:** [Text has enhanced contrast](https://www.w3.org/WAI/standards-guidelines/act/rules/09o5cg/); [Text has minimum contrast](https://www.w3.org/WAI/standards-guidelines/act/rules/afw4f7/)
- **Pass/fail example:**

  Pass:

  ```css
  .muted { color: #595959; background: #ffffff; } /* 7.0:1 */
  .btn { background: #b35900; color: #ffffff; }    /* >4.5:1 */
  ```

  Fail:

  ```css
  .muted { color: #aaaaaa; background: #ffffff; } /* 2.3:1 */
  .btn { background: #ff9900; color: #ffffff; }    /* 2.1:1 */
  ```

<a id="wcag-1-4-4"></a>
### WCAG-1.4.4 — Resize Text (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#resize-text> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html>

- **Text:**

  > Except for captions and images of text, text can be resized without assistive technology up to 200 percent without loss of content or functionality.

- **Applies to:** text, containers with fixed heights, viewport meta settings, responsive layouts
- **Testability:** assisted — axe-core meta-viewport flags `user-scalable=no` or `maximum-scale` below 2 that block zoom. A static scanner can flag fixed `height` on text containers and text sized in `px` inside `vw` units; a page runner can apply 200% text zoom and detect clipped or overlapping text via bounding boxes. Human confirms no loss of content or function.
  - **axe-core rules (4.13.0):** `meta-viewport`
- **Test procedure:**
  1. Set browser zoom to 200% (and, if possible, text-only zoom to 200%).
  2. Check all text remains visible, not clipped, truncated or overlapping.
  3. Check all functionality remains available.
  4. Check the viewport meta tag does not disable zoom.
- **Common failures:**
  - F69 — Failure of Success Criterion 1.4.4 when resizing visually rendered text up to 200 percent causes the text, image or controls to be clipped, truncated or obscured
  - F80 — Failure of Success Criterion 1.4.4 when text-based form controls do not resize when visually rendered text is resized up to 200%
  - F94 — Failure of Success Criterion 1.4.4 due to incorrect use of viewport units to resize text
  - Pattern: `<meta name="viewport" content="width=device-width, user-scalable=no">`.
  - Pattern: Fixed `height: 40px; overflow: hidden` on a container whose text grows.
  - Pattern: Font sizes set only in `vw` so text does not grow with zoom.
- **Sufficient techniques:**
  - G142 — Using a technology that has commonly-available user agents that support zoom
  - C28 — Specifying the size of text containers using em units
  - C12 — Using percent for font sizes
  - C13 — Using named font sizes
  - C14 — Using em units for font sizes
  - SCR34 — Calculating size and position in a way that scales with text size
  - G146 — Using liquid layout
  - G178 — Providing controls on the web page that allow users to incrementally change the size of all text on the page up to 200 percent
  - G179 — Ensuring that there is no loss of content or functionality when the text resizes and text containers do not change their width
- **ACT test rules:** [Meta viewport allows for zoom](https://www.w3.org/WAI/standards-guidelines/act/rules/b4f0c3/); [Zoomed text node is not clipped with CSS overflow](https://www.w3.org/WAI/standards-guidelines/act/rules/59br37/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>.card { min-height: 3rem; }</style>
  ```

  Fail:

  ```html
  <meta name="viewport" content="width=device-width, maximum-scale=1, user-scalable=no">
  <style>.card { height: 48px; overflow: hidden; }</style>
  ```

<a id="wcag-1-4-5"></a>
### WCAG-1.4.5 — Images of Text (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#images-of-text> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/images-of-text.html>

- **Text:**

  > If the technologies being used can achieve the visual presentation, text is used to convey information rather than images of text except for the following:
  >
  > - **Customizable:** The image of text can be visually customized to the user's requirements;
  > - **Essential:** A particular presentation of text is essential to the information being conveyed.
  >
  > *Note:* Logotypes (text that is part of a logo or brand name) are considered essential.

- **Applies to:** images of text: banners, buttons, headings rendered as images, text in canvas, scanned documents
- **Testability:** assisted — No axe-core rule applies. A static scanner can flag images with long `alt` text or filenames suggesting text (e.g. `heading.png`, `btn-*.png`); a page runner can OCR images for text. A human decides whether real text could achieve the same presentation or the image is essential/customisable.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify images that contain text.
  2. Exclude logos and cases where the particular presentation is essential.
  3. For the rest, judge whether the same visual result could be achieved with styled text.
  4. Where the image is user-customisable (font, size, color), note it as allowed.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Heading rendered as `<img src="welcome-heading.png" alt="Welcome">`.
  - Pattern: Button labels baked into PNG sprites.
  - Pattern: Quote graphics in body content instead of styled `<blockquote>`.
- **Sufficient techniques:**
  - C22 — Using CSS to control visual presentation of text
  - C30 — Using CSS to replace text with images of text and providing user interface controls to switch
  - G140 — Separating information and structure from presentation to enable different presentations
  - PDF7 — Performing OCR on a scanned PDF document to provide actual text
- **ACT test rules:** [HTML images contain no text](https://www.w3.org/WAI/standards-guidelines/act/rules/0va7u6/)
- **Pass/fail example:**

  Pass:

  ```html
  <h1 class="hero-title">Summer Sale</h1>
  <style>.hero-title { font: 700 3rem/1.1 "Brand Sans"; color: #fff; }</style>
  ```

  Fail:

  ```html
  <h1><img src="summer-sale-title.png" alt="Summer Sale"></h1>
  ```

<a id="wcag-1-4-6"></a>
### WCAG-1.4.6 — Contrast (Enhanced) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#contrast-enhanced> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/contrast-enhanced.html>

- **Text:**

  > The visual presentation of text and images of text has a contrast ratio of at least 7:1, except for the following:
  >
  > - **Large Text:** Large-scale text and images of large-scale text have a contrast ratio of at least 4.5:1;
  > - **Incidental:** Text or images of text that are part of an inactive user interface component, that are pure decoration, that are not visible to anyone, or that are part of a picture that contains significant other visual content, have no contrast requirement.
  > - **Logotypes:** Text that is part of a logo or brand name has no contrast requirement.

- **Applies to:** text, images of text, placeholder text, link and button text
- **Testability:** automated — axe-core color-contrast-enhanced computes ratios against 7:1 / 4.5:1, returning needs-review for text over images or gradients. A page runner can sample pixels behind text; human review covers images of text and incomplete results.
  - **axe-core rules (4.13.0):** `color-contrast-enhanced`
- **Test procedure:**
  1. Run an automated enhanced-contrast check.
  2. Measure flagged and incomplete items with a contrast analyser.
  3. Apply thresholds: 7:1 for normal text, 4.5:1 for large text.
  4. Exempt disabled components, decoration, incidental text and logos.
- **Common failures:**
  - F24 — Failure of Success Criterion 1.4.3, 1.4.6 and 1.4.8 due to specifying foreground colors without specifying background colors or vice versa
  - F83 — Failure of Success Criterion 1.4.3 and 1.4.6 due to using background images that do not provide sufficient contrast with foreground text (or images of text)
  - Pattern: Body text `#666` on white (5.7:1) passes AA but fails AAA.
  - Pattern: Link color `#0066cc` on white (5.6:1) below 7:1.
- **Sufficient techniques:**
  - G17 — Ensuring that a contrast ratio of at least 7:1 exists between text (and images of text) and background behind the text
  - G148 — Not specifying background color, not specifying text color, and not using technology features that change those defaults
  - G174 — Providing a control with a sufficient contrast ratio that allows users to switch to a presentation that uses sufficient contrast
  - G18 — Ensuring that a contrast ratio of at least 4.5:1 exists between text (and images of text) and background behind the text
- **ACT test rules:** [Text has enhanced contrast](https://www.w3.org/WAI/standards-guidelines/act/rules/09o5cg/); [Text has minimum contrast](https://www.w3.org/WAI/standards-guidelines/act/rules/afw4f7/)
- **Pass/fail example:**

  Pass:

  ```css
  body { color: #333333; background: #ffffff; } /* 12.6:1 */
  ```

  Fail:

  ```css
  body { color: #666666; background: #ffffff; } /* 5.7:1 */
  ```

<a id="wcag-1-4-7"></a>
### WCAG-1.4.7 — Low or No Background Audio (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#low-or-no-background-audio> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/low-or-no-background-audio.html>

- **Text:**

  > For prerecorded audio-only content that (1) contains primarily speech in the foreground, (2) is not an audio CAPTCHA or audio logo, and (3) is not vocalization intended to be primarily musical expression such as singing or rapping, at least one of the following is true:
  >
  > - **No Background:** The audio does not contain background sounds.
  > - **Turn Off:** The background sounds can be turned off.
  > - **20 dB:** The background sounds are at least 20 decibels lower than the foreground speech content, with the exception of occasional sounds that last for only one or two seconds.
  >   *Note:* Per the definition of "decibel," background sound that meets this requirement will be approximately four times quieter than the foreground speech content.

- **Applies to:** prerecorded audio-only content containing speech
- **Testability:** manual — No automated rule applies. A human listens to judge whether background sound is absent, can be turned off, or is at least 20 dB lower than speech (measured with audio tools if needed).
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify prerecorded audio-only speech content (not music, not CAPTCHA).
  2. Listen for background sounds under the speech.
  3. Confirm there is no background, an option to turn it off, or it is at least 20 dB quieter than foreground speech.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Podcast with loud music bed under the narration and no clean version.
  - Pattern: Audio instructions with ambient noise at near-speech volume.
- **Sufficient techniques:**
  - G56 — Mixing audio files so that non-speech sounds are at least 20 decibels lower than the speech audio content
- **Pass/fail example:**

  Pass:

  ```html
  <audio controls src="lesson-voice-only.mp3"></audio>
  <a href="lesson-with-music.mp3">Version with background music</a>
  ```

  Fail:

  ```html
  <audio controls src="lesson-music-bed.mp3"></audio>
  ```

<a id="wcag-1-4-8"></a>
### WCAG-1.4.8 — Visual Presentation (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#visual-presentation> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html>

- **Text:**

  > For the visual presentation of blocks of text, a mechanism is available to achieve the following:
  >
  > - Foreground and background colors can be selected by the user.
  > - Width is no more than 80 characters or glyphs (40 if CJK).
  > - Text is not justified (aligned to both the left and the right margins).
  > - Line spacing (leading) is at least space-and-a-half within paragraphs, and paragraph spacing is at least 1.5 times larger than the line spacing.
  > - Text can be resized without assistive technology up to 200 percent in a way that does not require the user to scroll horizontally to read a line of text on a full-screen window.
  >
  > *Note 1:* Content is not required to use these values. The requirement is that a mechanism is available for users to change these presentation aspects. The mechanism can be provided by the browser or other user agent. Content is not required to provide the mechanism.
  >
  > *Note 2:* Writing systems for some languages use different presentation aspects to improve readability and legibility. If a presentation aspect in this success criterion is not used in a writing system, content in that writing system does not need to use that presentation setting and can conform without it. Authors are encouraged to follow guidance for improving readability and legibility of text in their writing system.

- **Applies to:** blocks of text: articles, documentation, long-form content
- **Testability:** assisted — No axe-core rule applies. A static scanner can flag `text-align: justify`, fixed `max-width` over 80ch, and `line-height` below 1.5; a page runner can measure line lengths and verify text reflows at 200% without horizontal scrolling. A human confirms that the colour selection mechanism exists.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Check users can select foreground and background colors (via user agent or a provided mechanism).
  2. Check line width is at most 80 characters (40 for CJK).
  3. Check text is not fully justified.
  4. Check line spacing is at least 1.5 within paragraphs and paragraph spacing at least 1.5x line spacing.
  5. Check text resizes to 200% without horizontal scrolling on a full-screen window.
- **Common failures:**
  - F24 — Failure of Success Criterion 1.4.3, 1.4.6 and 1.4.8 due to specifying foreground colors without specifying background colors or vice versa
  - F88 — Failure of Success Criterion 1.4.8 due to using text that is justified (aligned to both the left and the right margins)
  - Pattern: `p { text-align: justify; }` on long passages.
  - Pattern: `.article { width: 1100px; }` producing ~150-character lines.
  - Pattern: `line-height: 1.1` on body text.
- **Sufficient techniques:**
  - C23 — Specifying text and background colors of secondary content such as banners, features and navigation in CSS while not specifying text and background colors of the main content
  - C25 — Specifying borders and layout in CSS to delineate areas of a web page while not specifying text and text-background colors
  - G156 — Using a technology that has commonly-available user agents that can change the foreground and background of blocks of text
  - G148 — Not specifying background color, not specifying text color, and not using technology features that change those defaults
  - G175 — Providing a multi color selection tool on the page for foreground and background colors
  - G204 — Not interfering with the user agent's reflow of text as the viewing window is narrowed
  - C20 — Using relative measurements to set column widths so that lines can average 80 characters or less when the browser is resized
  - C19 — Specifying alignment either to the left or right in CSS
  - G172 — Providing a mechanism to remove full justification of text
  - G169 — Aligning text on only one side
  - G188 — Providing a button on the page to increase line spaces and paragraph spaces
  - C21 — Specifying line spacing in CSS
  - G146 — Using liquid layout
  - C12 — Using percent for font sizes
  - C13 — Using named font sizes
  - C14 — Using em units for font sizes
  - C24 — Using percentage values in CSS for container sizes
  - SCR34 — Calculating size and position in a way that scales with text size
  - G206 — Providing options within the content to switch to a layout that does not require the user to scroll horizontally to read a line of text
- **Pass/fail example:**

  Pass:

  ```css
  .article { max-width: 70ch; line-height: 1.6; text-align: start; }
  .article p { margin-block-end: 1.6em; }
  ```

  Fail:

  ```css
  .article { width: 1100px; line-height: 1.1; text-align: justify; }
  ```

<a id="wcag-1-4-9"></a>
### WCAG-1.4.9 — Images of Text (No Exception) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#images-of-text-no-exception> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/images-of-text-no-exception.html>

- **Text:**

  > Images of text are only used for pure decoration or where a particular presentation of text is essential to the information being conveyed.
  >
  > *Note:* Logotypes (text that is part of a logo or brand name) are considered essential.

- **Applies to:** images of text of any kind
- **Testability:** manual — No automated rule applies. A static scanner or OCR-based page runner can list images containing text; a human confirms each is decoration or essential (logos count as essential).
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify all images of text.
  2. Confirm each is purely decorative or its text presentation is essential (e.g. logo, font specimen).
  3. Any other image of text fails at this level.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Infographic with key statistics only in the image.
  - Pattern: Navigation buttons rendered as text images.
- **Sufficient techniques:**
  - C22 — Using CSS to control visual presentation of text
  - C30 — Using CSS to replace text with images of text and providing user interface controls to switch
  - G140 — Separating information and structure from presentation to enable different presentations
  - PDF7 — Performing OCR on a scanned PDF document to provide actual text
- **ACT test rules:** [HTML images contain no text](https://www.w3.org/WAI/standards-guidelines/act/rules/0va7u6/)
- **Pass/fail example:**

  Pass:

  ```html
  <figure>
    <img src="chart.svg" alt="">
    <figcaption>Revenue grew 12% in Q3.</figcaption>
  </figure>
  ```

  Fail:

  ```html
  <img src="revenue-callout.png" alt="Revenue grew 12% in Q3">
  ```

<a id="wcag-1-4-10"></a>
### WCAG-1.4.10 — Reflow (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#reflow> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/reflow.html>

- **Text:**

  > Content can be presented without loss of information or functionality, and without requiring scrolling in two dimensions for:
  >
  > - Vertical scrolling content at a width equivalent to 320 CSS pixels;
  > - Horizontal scrolling content at a height equivalent to 256 CSS pixels.
  >
  > Except for parts of the content which require two-dimensional layout for usage or meaning.
  >
  > *Note 1:* 320 CSS pixels is equivalent to a starting viewport width of 1280 CSS pixels wide at 400% zoom. For web content which is designed to scroll horizontally (e.g., with vertical text), 256 CSS pixels is equivalent to a starting viewport height of 1024 CSS pixels at 400% zoom.
  >
  > *Note 2:* Examples of content which requires two-dimensional layout are images required for understanding (such as maps and diagrams), video, games, presentations, data tables (not individual cells), and interfaces where it is necessary to keep toolbars in view while manipulating content. It is acceptable to provide two-dimensional scrolling for such parts of the content.

- **Applies to:** responsive layouts, fixed-width containers, sticky headers, tables, carousels, modals
- **Testability:** assisted — No axe-core rule applies. A static scanner can flag fixed `width` in px on layout containers, `min-width` above 320px and `white-space: nowrap` on long text; a page runner can set a 320 CSS px wide viewport (1280px at 400%) and detect horizontal scroll (`scrollWidth > clientWidth`) and clipped elements. A human confirms no content or function is lost and exceptions (data tables, maps) apply.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Set the viewport to 1280px wide and zoom to 400% (equivalently a 320 CSS px viewport).
  2. Check vertical-scrolling content does not require horizontal scrolling.
  3. Check no content or functionality is lost, hidden or overlapping.
  4. Allow two-dimensional scrolling only for content that needs it (data tables, maps, diagrams, toolbars).
- **Common failures:**
  - F102 — Failure of Success Criterion 1.4.10 due to content disappearing and not being available when content has reflowed
  - Pattern: `.container { width: 960px; }` with no responsive breakpoint.
  - Pattern: Sticky header and footer that cover most of the viewport at 400% zoom.
  - Pattern: Long URLs or code with `white-space: nowrap` forcing page-level horizontal scroll.
  - Pattern: Content hidden with `display:none` at narrow breakpoints and not available elsewhere.
- **Sufficient techniques:**
  - C32 — Using media queries and grid CSS to reflow columns
  - C31 — Using CSS Flexbox to reflow content
  - C33 — Allowing for Reflow with Long URLs and Strings of Text
  - C38 — Using CSS width, max-width and flexbox to fit labels and inputs
  - SCR34 — Calculating size and position in a way that scales with text size
  - G206 — Providing options within the content to switch to a layout that does not require the user to scroll horizontally to read a line of text
  - G224 — Accounting for meaningful text indentation and Reflow
  - G225 — Section panels that scroll horizontally are designed to fit within a width of 320 CSS pixels on a vertically scrolling page
- **ACT test rules:** [Meta viewport allows for zoom](https://www.w3.org/WAI/standards-guidelines/act/rules/b4f0c3/)
- **Pass/fail example:**

  Pass:

  ```css
  .container { max-width: 60rem; width: 100%; }
  .url { overflow-wrap: anywhere; }
  ```

  Fail:

  ```css
  .container { width: 960px; }
  .url { white-space: nowrap; }
  ```

<a id="wcag-1-4-11"></a>
### WCAG-1.4.11 — Non-text Contrast (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#non-text-contrast> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html>

- **Text:**

  > The visual presentation of the following have a contrast ratio of at least 3:1 against adjacent color(s):
  >
  > - **User Interface Components:** Visual information required to identify user interface components and states, except for inactive components or where the appearance of the component is determined by the user agent and not modified by the author;
  > - **Graphical Objects:** Parts of graphics required to understand the content, except when a particular presentation of graphics is essential to the information being conveyed.

- **Applies to:** UI component boundaries (inputs, buttons, checkboxes), focus indicators, icons, chart elements, state indicators
- **Testability:** assisted — axe-core does not test non-text contrast. A static scanner can compute contrast for CSS `border-color`/`outline-color` against declared backgrounds; a page runner can sample computed border, outline and icon colors against adjacent pixels. A human decides which visuals are required to identify the component or state.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify visual information needed to perceive UI components and their states (borders, checkmarks, focus rings, toggle positions).
  2. Measure contrast against adjacent colors; require at least 3:1.
  3. Identify graphical objects required to understand content (chart lines, icons) and measure 3:1 against adjacent colors.
  4. Exempt inactive components and appearance entirely determined by the user agent.
- **Common failures:**
  - F78 — Failure of Success Criterion 1.4.11, 2.4.7 and 2.4.13 due to styling element outlines and borders in a way that removes or renders non-visible the visual focus indicator
  - Pattern: Text input with `border: 1px solid #ddd` on white (1.4:1) as the only field boundary.
  - Pattern: Custom checkbox with a pale checkmark that does not reach 3:1 against its box.
  - Pattern: Focus ring `outline-color: #a0c4ff` on white.
  - Pattern: Icon-only button whose icon is `#bbb` on white.
- **Sufficient techniques:**
  - G174 — Providing a control with a sufficient contrast ratio that allows users to switch to a presentation that uses sufficient contrast
  - G195 — Using an author-supplied, visible focus indicator
  - C40 — Creating a two-color focus indicator to ensure sufficient contrast with all components
  - G207 — Ensuring that a contrast ratio of 3:1 is provided for icons
  - G209 — Provide sufficient contrast at the boundaries between adjoining colors
- **Pass/fail example:**

  Pass:

  ```css
  input { border: 1px solid #767676; } /* 4.5:1 on white */
  :focus-visible { outline: 2px solid #1a5fb4; }
  ```

  Fail:

  ```css
  input { border: 1px solid #e0e0e0; } /* 1.3:1 on white */
  :focus-visible { outline: 2px solid #cfe2ff; }
  ```

<a id="wcag-1-4-12"></a>
### WCAG-1.4.12 — Text Spacing (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#text-spacing> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html>

- **Text:**

  > In content implemented using markup languages that support the following text style properties, no loss of content or functionality occurs by setting all of the following and by changing no other style property:
  >
  > - Line height (line spacing) to at least 1.5 times the font size;
  > - Spacing following paragraphs to at least 2 times the font size;
  > - Letter spacing (tracking) to at least 0.12 times the font size;
  > - Word spacing to at least 0.16 times the font size.
  >
  > Exception: Human languages and scripts that do not make use of one or more of these text style properties in written text can conform using only the properties that exist for that combination of language and script.
  >
  > *Note 1:* Content is not required to use these text spacing values. The requirement is to ensure that when a user overrides the authored text spacing, content or functionality is not lost.
  >
  > *Note 2:* Writing systems for some languages use different text spacing settings, such as paragraph start indent. Authors are encouraged to follow locally available guidance for improving readability and legibility of text in their writing system.

- **Applies to:** text containers, buttons, cards, navigation items, fixed-height components
- **Testability:** assisted — axe-core avoid-inline-spacing flags inline `style` with `!important` spacing that users cannot override. A page runner can inject the text-spacing bookmarklet values (line-height 1.5, paragraph spacing 2em, letter-spacing 0.12em, word-spacing 0.16em) and detect overflow/clipping via bounding boxes; a static scanner can flag fixed heights with `overflow: hidden`. A human confirms no loss of content.
  - **axe-core rules (4.13.0):** `avoid-inline-spacing`
- **Test procedure:**
  1. Apply the text-spacing overrides: line-height 1.5, paragraph spacing 2x font size, letter spacing 0.12x, word spacing 0.16x.
  2. Check all text remains visible, not clipped, truncated or overlapping.
  3. Check controls and labels remain usable.
  4. Check author styles do not block the overrides (`!important` inline spacing).
- **Common failures:**
  - F104 — Failure of Success Criterion 1.4.12 due to clipped or overlapped content when text spacing is adjusted
  - Pattern: Button `height: 32px; overflow: hidden` so text is clipped when line-height grows.
  - Pattern: Inline `style="letter-spacing: 0 !important"` on text.
  - Pattern: Card with fixed height truncating content after spacing increases.
- **Sufficient techniques:**
  - C36 — Allowing for text spacing override
  - C35 — Allowing for text spacing without wrapping
- **ACT test rules:** [Important letter spacing in style attributes is wide enough](https://www.w3.org/WAI/standards-guidelines/act/rules/24afc2/); [Important line height in style attributes is wide enough](https://www.w3.org/WAI/standards-guidelines/act/rules/78fd32/); [Important word spacing in style attributes is wide enough](https://www.w3.org/WAI/standards-guidelines/act/rules/9e45ec/)
- **Pass/fail example:**

  Pass:

  ```css
  .btn { min-height: 2.75rem; padding: .5em 1em; }
  .card { min-height: 10rem; }
  ```

  Fail:

  ```css
  .btn { height: 32px; overflow: hidden; white-space: nowrap; }
  .card { height: 160px; overflow: hidden; }
  ```

<a id="wcag-1-4-13"></a>
### WCAG-1.4.13 — Content on Hover or Focus (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#content-on-hover-or-focus> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html>

- **Text:**

  > Where receiving and then removing pointer hover or keyboard focus triggers additional content to become visible and then hidden, the following are true:
  >
  > - **Dismissible:** A mechanism is available to dismiss the additional content without moving pointer hover or keyboard focus, unless the additional content communicates an input error or does not obscure or replace other content;
  > - **Hoverable:** If pointer hover can trigger the additional content, then the pointer can be moved over the additional content without the additional content disappearing;
  > - **Persistent:** The additional content remains visible until the hover or focus trigger is removed, the user dismisses it, or its information is no longer valid.
  >
  > Exception: The visual presentation of the additional content is controlled by the user agent and is not modified by the author.
  >
  > *Note 1:* Examples of additional content controlled by the user agent include browser tooltips created through use of the HTML `title` attribute [HTML].
  >
  > *Note 2:* Custom tooltips, sub-menus, and other nonmodal popups that display on hover and focus are examples of additional content covered by this criterion.
  >
  > *Note 3:* This criterion applies to content that appears in addition to the triggering component itself. Since hidden components that are made visible on keyboard focus (such as links used to skip to another part of a page) do not present additional content they are not covered by this criterion.

- **Applies to:** tooltips, hover cards, custom dropdowns, popovers and content revealed on hover or focus
- **Testability:** assisted — No axe-core rule applies. A static scanner can flag `:hover`-only reveal CSS and `mouseenter`/`mouseleave` handlers without Escape handling; a page runner can hover/focus triggers and check whether content disappears when the pointer moves onto it or on Escape. Human confirmation is required.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Find content that appears on pointer hover or keyboard focus.
  2. Dismissible: confirm it can be dismissed (e.g. Escape) without moving pointer or focus, unless it obscures nothing or conveys an input error.
  3. Hoverable: move the pointer onto the new content and confirm it stays visible.
  4. Persistent: confirm it stays until hover/focus is removed, the user dismisses it, or its info is no longer valid.
- **Common failures:**
  - F95 — Failure of Success Criterion 1.4.13 due to content shown on hover not being hoverable
  - Pattern: Tooltip that closes on `mouseleave` of the trigger so users cannot move onto it.
  - Pattern: Hover card that covers content and has no Escape handler.
  - Pattern: Tooltip that disappears after a timeout.
  - Pattern: CSS `.trigger:hover + .tip { display:block }` with no focus equivalent.
- **Sufficient techniques:**
  - SCR39 — Making content on focus or hover hoverable, dismissible, and persistent
- **Pass/fail example:**

  Pass:

  ```jsx
  <span onMouseEnter={open} onFocus={open}
        onKeyDown={e => e.key === "Escape" && close()}>
    <button aria-describedby="tip">Info</button>
    {isOpen && <div id="tip" role="tooltip"
      onMouseLeave={close}>Details</div>}
  </span>
  ```

  Fail:

  ```jsx
  <button onMouseEnter={open} onMouseLeave={close}>
    Info
  </button>
  {isOpen && <div role="tooltip">Details</div>}
  {/* closes when pointer leaves trigger; no Escape */}
  ```
