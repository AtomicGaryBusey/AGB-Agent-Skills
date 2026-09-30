# WCAG 2.2 glossary (defined terms)

> **Source and licence.** Normative text quoted in this file (marked as block quotes, i.e. every definition) is copied verbatim from
> *Web Content Accessibility Guidelines (WCAG) 2.2*, W3C Recommendation, 12 December 2024 edition,
> <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide Web Consortium.
> <https://www.w3.org/copyright/document-license-2023/>. Status: W3C Recommendation.
> All other text (summaries, testability, procedures, code patterns and examples) is original to this skill.
> See `NOTICE` at the skill root.

All terms defined in WCAG 2.2 section 6 (Glossary), in the specification's order, with verbatim definitions. "Used by" lists the success criteria whose normative text links to the term (computed from the spec's markup). Terms auditors most often need when deciding pass/fail are marked **(key)**.

## Index

[abbreviation](#dfn-abbreviations), [accessibility supported](#dfn-accessibility-supported), [alternative for time-based media](#dfn-alternative-for-time-based-media), [ambiguous to users in general](#dfn-ambiguous-to-users-in-general), [ASCII art](#dfn-ascii-art), [assistive technology (as used in this document)](#dfn-assistive-technologies), [audio](#dfn-audio), [audio description](#dfn-audio-descriptions), [audio-only](#dfn-audio-only), [blinking](#dfn-blinking), [blocks of text](#dfn-blocks-of-text), [CAPTCHA](#dfn-captcha), [captions](#dfn-captions), [changes of context](#dfn-change-of-context), [cognitive function test](#dfn-cognitive-function-test), [conformance](#dfn-conform), [conforming alternate version](#dfn-conforming-alternate-versions), [content (web content)](#dfn-content), [context-sensitive help](#dfn-context-sensitive-help), [contrast ratio](#dfn-contrast-ratio), [correct reading sequence](#dfn-correct-reading-sequence), [CSS pixel](#dfn-css-pixels), [down-event](#dfn-down-event), [dragging movement](#dfn-dragging-movements), [emergency](#dfn-emergency), [essential](#dfn-essential), [extended audio description](#dfn-extended-audio-description), [flash](#dfn-flashes), [focus indicator](#dfn-focus-indicator), [functionality](#dfn-functionality), [general flash and red flash thresholds](#dfn-general-flash-and-red-flash-thresholds), [human language](#dfn-human-language-s), [idiom](#dfn-idioms), [image of text](#dfn-images-of-text), [informative](#dfn-informative), [input error](#dfn-input-error), [jargon](#dfn-jargon), [keyboard interface](#dfn-keyboard-interface), [keyboard shortcut](#dfn-keyboard-shortcuts), [label](#dfn-labels), [large scale (text)](#dfn-large-scale), [legal commitments](#dfn-legal-commitments), [link purpose](#dfn-purpose-of-each-link), [live](#dfn-live), [lower secondary education level](#dfn-lower-secondary-education-level), [mechanism](#dfn-mechanism), [media alternative for text](#dfn-media-alternative-for-text), [motion animation](#dfn-motion-animation), [minimum bounding box](#dfn-bounding-boxes), [name](#dfn-name), [navigated sequentially](#dfn-navigated-sequentially), [non-text content](#dfn-non-text-content), [normative](#dfn-normative), [on a full-screen window](#dfn-on-a-full-screen-window), [paused](#dfn-pause), [perimeter](#dfn-perimeter), [pointer input](#dfn-pointer-inputs), [prerecorded](#dfn-prerecorded), [presentation](#dfn-presentation), [primary education level](#dfn-primary-education), [process](#dfn-processes), [programmatically determined (programmatically determinable)](#dfn-programmatically-determinable), [programmatically determined link context](#dfn-programmatically-determined-link-context), [programmatically set](#dfn-programmatically-set), [pure decoration](#dfn-pure-decoration), [real-time event](#dfn-real-time-events), [region](#dfn-regions), [relationships](#dfn-relationships), [relative luminance](#dfn-relative-luminance), [relied upon (technologies that are)](#dfn-relied-upon), [role](#dfn-role), [same functionality](#dfn-same-functionality), [same relative order](#dfn-same-relative-order), [satisfies a success criterion](#dfn-satisfies), [section](#dfn-section), [set of web pages](#dfn-set-of-web-pages), [sign language](#dfn-sign-language), [sign language interpretation](#dfn-sign-language-interpretation), [single pointer](#dfn-single-pointer), [specific sensory experience](#dfn-specific-sensory-experience), [state](#dfn-states), [status message](#dfn-status-messages), [structure](#dfn-structure), [style property](#dfn-style-properties), [supplemental content](#dfn-supplementary-content), [synchronized media](#dfn-synchronized-media), [target](#dfn-targets), [technology (web content)](#dfn-technologies), [text](#dfn-text), [text alternative](#dfn-text-alternative), [up-event](#dfn-up-event), [used in an unusual or restricted way](#dfn-used-in-an-unusual-or-restricted-way), [user agent](#dfn-user-agents), [user-controllable](#dfn-user-controllable), [user interface component](#dfn-user-interface-components), [user inactivity](#dfn-user-inactivity), [video](#dfn-video), [video-only](#dfn-video-only), [viewport](#dfn-viewport), [visually customized](#dfn-visually-customized), [web page](#dfn-web-page-s)

<a id="dfn-abbreviations"></a>
### abbreviation

> shortened form of a word, phrase, or name where the abbreviation has not become part of the language
>
> *Note 1:* This includes initialisms and acronyms where:
>
> 1. **initialisms** are shortened forms of a name or phrase made from the initial letters of words or syllables contained in that name or phrase
>   *Note 2:* Not defined in all languages.
>   *Example 1:* SNCF is a French initialism that contains the initial letters of the Société Nationale des Chemins de Fer, the French national railroad.
>   *Example 2:* ESP is an initialism for extrasensory perception.
> 2. **acronyms** are abbreviated forms made from the initial letters or parts of other words (in a name or phrase) which may be pronounced as a word
>   *Example 3:* NOAA is an acronym made from the initial letters of the National Oceanic and Atmospheric Administration in the United States.
>
> *Note 3:* Some companies have adopted what used to be an initialism as their company name. In these cases, the new name of the company is the letters (for example, Ecma) and the word is no longer considered an abbreviation.

Used by: WCAG-3.1.4 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-abbreviations>

<a id="dfn-accessibility-supported"></a>
### accessibility supported (key)

> supported by users' assistive technologies as well as the accessibility features in browsers and other user agents
>
> To qualify as an accessibility-supported use of a web content technology (or feature of a technology), both 1 and 2 must be satisfied for a web content technology (or feature):
>
> 1. **The way that the web content technology is used must be supported by users' assistive technology (AT).**  This means that the way that the technology is used has been tested for interoperability with users' assistive technology in the human language(s) of the content,
>   **AND**
> 2. **The web content technology must have accessibility-supported user agents that are available to users.**  This means that at least one of the following four statements is true:
>   1. The technology is supported natively in widely-distributed user agents that are also accessibility supported (such as HTML and CSS);
>     **OR**
>   2. The technology is supported in a widely-distributed plug-in that is also accessibility supported;
>     **OR**
>   3. The content is available in a closed environment, such as a university or corporate network, where the user agent required by the technology and used by the organization is also accessibility supported;
>     **OR**
>   4. The user agent(s) that support the technology are accessibility supported and are available for download or purchase in a way that:
>     - does not cost a person with a disability any more than a person without a disability **and**
>     - is as easy to find and obtain for a person with a disability as it is for a person without disabilities.
>
> *Note 1:* The Accessibility Guidelines Working Group and the W3C do not specify which or how much support by assistive technologies there must be for a particular use of a web technology in order for it to be classified as accessibility supported. (See Level of Assistive Technology Support Needed for "Accessibility Support".)
>
> *Note 2:* Web technologies can be used in ways that are not accessibility supported as long as they are not relied upon and the page as a whole meets the conformance requirements, including Conformance Requirement 4 and Conformance Requirement 5.
>
> *Note 3:* When a web technology is used in a way that is "accessibility supported," it does not imply that the entire technology or all uses of the technology are supported. Most technologies, including HTML, lack support for at least one feature or use. Pages conform to WCAG only if the uses of the technology that are accessibility supported can be relied upon to meet WCAG requirements.
>
> *Note 4:* When citing web content technologies that have multiple versions, the version(s) supported should be specified.
>
> *Note 5:* One way for authors to locate uses of a technology that are accessibility supported would be to consult compilations of uses that are documented to be accessibility supported. (See Understanding Accessibility-Supported Web Technology Uses.) Authors, companies, technology vendors, or others may document accessibility-supported ways of using web content technologies. However, all ways of using technologies in the documentation would need to meet the definition of accessibility-supported Web content technologies above.

Used by: WCAG-2.5.4 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-accessibility-supported>

<a id="dfn-alternative-for-time-based-media"></a>
### alternative for time-based media

> document including correctly sequenced text descriptions of time-based visual and auditory information and providing a means for achieving the outcomes of any time-based interaction
>
> *Note:* A screenplay used to create the synchronized media content would meet this definition only if it was corrected to accurately represent the final synchronized media after editing.

Used by: WCAG-1.2.1, WCAG-1.2.3, WCAG-1.2.8, WCAG-1.2.9 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-alternative-for-time-based-media>

<a id="dfn-ambiguous-to-users-in-general"></a>
### ambiguous to users in general

> the purpose cannot be determined from the link and all information of the web page presented to the user simultaneously with the link (i.e., readers without disabilities would not know what a link would do until they activated it)
>
> *Example:* The word guava in the following sentence "One of the notable exports is guava" is a link. The link could lead to a definition of guava, a chart listing the quantity of guava exported or a photograph of people harvesting guava. Until the link is activated, all readers are unsure and the person with a disability is not at any disadvantage.

Used by: WCAG-2.4.4, WCAG-2.4.9 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-ambiguous-to-users-in-general>

<a id="dfn-ascii-art"></a>
### ASCII art

> picture created by a spatial arrangement of characters or glyphs (typically from the 95 printable characters defined by ASCII)

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-ascii-art>

<a id="dfn-assistive-technologies"></a>
### assistive technology (as used in this document)

> hardware and/or software that acts as a user agent, or along with a mainstream user agent, to provide functionality to meet the requirements of users with disabilities that go beyond those offered by mainstream user agents
>
> *Note 1:* Functionality provided by assistive technology includes alternative presentations (e.g., as synthesized speech or magnified content), alternative input methods (e.g., voice), additional navigation or orientation mechanisms, and content transformations (e.g., to make tables more accessible).
>
> *Note 2:* Assistive technologies often communicate data and messages with mainstream user agents by using and monitoring APIs.
>
> *Note 3:* The distinction between mainstream user agents and assistive technologies is not absolute. Many mainstream user agents provide some features to assist individuals with disabilities. The basic difference is that mainstream user agents target broad and diverse audiences that usually include people with and without disabilities. Assistive technologies target narrowly defined populations of users with specific disabilities. The assistance provided by an assistive technology is more specific and appropriate to the needs of its target users. The mainstream user agent may provide important functionality to assistive technologies like retrieving web content from program objects or parsing markup into identifiable bundles.
>
> *Example:* Assistive technologies that are important in the context of this document include the following:
>
> - screen magnifiers, and other visual reading assistants, which are used by people with visual, perceptual and physical print disabilities to change text font, size, spacing, color, synchronization with speech, etc. in order to improve the visual readability of rendered text and images;
> - screen readers, which are used by people who are blind to read textual information through synthesized speech or braille;
> - text-to-speech software, which is used by some people with cognitive, language, and learning disabilities to convert text into synthetic speech;
> - speech recognition software, which may be used by people who have some physical disabilities;
> - alternative keyboards, which are used by people with certain physical disabilities to simulate the keyboard (including alternate keyboards that use head pointers, single switches, sip/puff and other special input devices.);
> - alternative pointing devices, which are used by people with certain physical disabilities to simulate mouse pointing and button activations.

Used by: WCAG-1.1.1, WCAG-1.4.4, WCAG-1.4.8, WCAG-4.1.2, WCAG-4.1.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-assistive-technologies>

<a id="dfn-audio"></a>
### audio

> the technology of sound reproduction
>
> *Note:* Audio can be created synthetically (including speech synthesis), recorded from real world sounds, or both.

Used by: WCAG-1.2.2, WCAG-1.2.4, WCAG-1.2.6 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-audio>

<a id="dfn-audio-descriptions"></a>
### audio description (key)

> narration added to the soundtrack to describe important visual details that cannot be understood from the main soundtrack alone
>
> *Note 1:* Audio description of video provides information about actions, characters, scene changes, on-screen text, and other visual content.
>
> *Note 2:* In standard audio description, narration is added during existing pauses in dialogue. (See also extended audio description.)
>
> *Note 3:* Where all of the video information is already provided in existing audio, no additional audio description is necessary.
>
> *Note 4:* Also called "video description" and "descriptive narration."

Used by: WCAG-1.2.3, WCAG-1.2.5, WCAG-1.2.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-audio-descriptions>

<a id="dfn-audio-only"></a>
### audio-only

> a time-based presentation that contains only audio (no video and no interaction)

Used by: WCAG-1.2.1, WCAG-1.2.9, WCAG-1.4.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-audio-only>

<a id="dfn-blinking"></a>
### blinking

> switch back and forth between two visual states in a way that is meant to draw attention
>
> *Note:* See also flash. It is possible for something to be large enough and blink brightly enough at the right frequency to be also classified as a flash.

Used by: WCAG-2.2.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-blinking>

<a id="dfn-blocks-of-text"></a>
### blocks of text (key)

> more than one sentence of text

Used by: WCAG-1.4.8, WCAG-2.5.5 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-blocks-of-text>

<a id="dfn-captcha"></a>
### CAPTCHA

> initialism for "Completely Automated Public Turing test to tell Computers and Humans Apart"
>
> *Note 1:* CAPTCHA tests often involve asking the user to type in text that is displayed in an obscured image or audio file.
>
> *Note 2:* A Turing test is any system of tests designed to differentiate a human from a computer. It is named after famed computer scientist Alan Turing. The term was coined by researchers at Carnegie Mellon University.

Used by: WCAG-1.1.1, WCAG-1.4.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-captcha>

<a id="dfn-captions"></a>
### captions (key)

> synchronized visual and/or text alternative for both speech and non-speech audio information needed to understand the media content
>
> *Note 1:* Captions are similar to dialogue-only subtitles except captions convey not only the content of spoken dialogue, but also equivalents for non-dialogue audio information needed to understand the program content, including sound effects, music, laughter, speaker identification and location.
>
> *Note 2:* Closed Captions are equivalents that can be turned on and off with some players.
>
> *Note 3:* Open Captions are any captions that cannot be turned off. For example, if the captions are visual equivalent images of text embedded in video.
>
> *Note 4:* Captions should not obscure or obstruct relevant information in the video.
>
> *Note 5:* In some countries, captions are called subtitles.
>
> *Note 6:* Audio descriptions can be, but do not need to be, captioned since they are descriptions of information that is already presented visually.

Used by: WCAG-1.2.2, WCAG-1.2.4, WCAG-1.4.4 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-captions>

<a id="dfn-change-of-context"></a>
### changes of context (key)

> major changes that, if made without user awareness, can disorient users who are not able to view the entire page simultaneously
>
> Changes in context include changes of:
>
> - user agent;
> - viewport;
> - focus;
> - content that changes the meaning of the web page
>
> *Note:* A change of content is not always a change of context. Changes in content, such as an expanding outline, dynamic menu, or a tab control do not necessarily change the context, unless they also change one of the above (e.g., focus).
>
> *Example:* Opening a new window, moving focus to a different component, going to a new page (including anything that would look to a user as if they had moved to a new page) or significantly re-arranging the content of a page are examples of changes of context.

Used by: WCAG-3.2.1, WCAG-3.2.2, WCAG-3.2.5 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-change-of-context>

<a id="dfn-cognitive-function-test"></a>
### cognitive function test (key) — new in 2.2

> A task that requires the user to remember, manipulate, or transcribe information. Examples include, but are not limited to:
>
> - memorization, such as remembering a username, password, set of characters, images, or patterns. The common identifiers name, e-mail, and phone number are not considered cognitive function tests as they are personal to the user and consistent across websites;
> - transcription, such as typing in characters;
> - use of correct spelling;
> - performance of calculations;
> - solving of puzzles.

Used by: WCAG-3.3.8, WCAG-3.3.9 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-cognitive-function-test>

<a id="dfn-conform"></a>
### conformance

> satisfying all the requirements of a given standard, guideline or specification

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-conform>

<a id="dfn-conforming-alternate-versions"></a>
### conforming alternate version (key)

> version that
>
> 1. conforms at the designated level, and
> 2. provides all of the same information and functionality in the same human language, and
> 3. is as up to date as the non-conforming content, and
> 4. for which at least one of the following is true:
>   1. the conforming version can be reached from the non-conforming page via an accessibility-supported mechanism, or
>   2. the non-conforming version can only be reached from the conforming version, or
>   3. the non-conforming version can only be reached from a conforming page that also provides a mechanism to reach the conforming version
>
> *Note 1:* In this definition, "can only be reached" means that there is some mechanism, such as a conditional redirect, that prevents a user from "reaching" (loading) the non-conforming page unless the user had just come from the conforming version.
>
> *Note 2:* The alternate version does not need to be matched page for page with the original (e.g., the conforming alternate version may consist of multiple pages).
>
> *Note 3:* If multiple language versions are available, then conforming alternate versions are required for each language offered.
>
> *Note 4:* Alternate versions may be provided to accommodate different technology environments or user groups. Each version should be as conformant as possible. One version would need to be fully conformant in order to meet conformance requirement 1.
>
> *Note 5:* The conforming alternative version does not need to reside within the scope of conformance, or even on the same website, as long as it is as freely available as the non-conforming version.
>
> *Note 6:* Alternate versions should not be confused with supplementary content, which support the original page and enhance comprehension.
>
> *Note 7:* Setting user preferences within the content to produce a conforming version is an acceptable mechanism for reaching another version as long as the method used to set the preferences is accessibility supported.
>
> See Understanding Conforming Alternate Versions

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-conforming-alternate-versions>

<a id="dfn-content"></a>
### content (web content) (key)

> information and sensory experience to be communicated to the user by means of a user agent, including code or markup that defines the content's structure, presentation, and interactions

Used by: WCAG-2.4.13 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-content>

<a id="dfn-context-sensitive-help"></a>
### context-sensitive help

> help text that provides information related to the function currently being performed
>
> *Note:* Clear labels can act as context-sensitive help.

Used by: WCAG-3.3.5 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-context-sensitive-help>

<a id="dfn-contrast-ratio"></a>
### contrast ratio (key)

> (L1 + 0.05) / (L2 + 0.05), where
>
> - L1 is the relative luminance of the lighter of the colors, and
> - L2 is the relative luminance of the darker of the colors.
>
> *Note 1:* Contrast ratios can range from 1 to 21 (commonly written 1:1 to 21:1).
>
> *Note 2:* Because authors do not have control over user settings as to how text is rendered (for example font smoothing or anti-aliasing), the contrast ratio for text can be evaluated with anti-aliasing turned off.
>
> *Note 3:* For the purpose of Success Criteria 1.4.3 and 1.4.6, contrast is measured with respect to the specified background over which the text is rendered in normal usage. If no background color is specified, then white is assumed.
>
> *Note 4:* Background color is the specified color of content over which the text is to be rendered in normal usage. It is a failure if no background color is specified when the text color is specified, because the user's default background color is unknown and cannot be evaluated for sufficient contrast. For the same reason, it is a failure if no text color is specified when a background color is specified.
>
> *Note 5:* When there is a border around the letter, the border can add contrast and would be used in calculating the contrast between the letter and its background. A narrow border around the letter would be used as the letter. A wide border around the letter that fills in the inner details of the letters acts as a halo and would be considered background.
>
> *Note 6:* WCAG conformance should be evaluated for color pairs specified in the content that an author would expect to appear adjacent in typical presentation. Authors need not consider unusual presentations, such as color changes made by the user agent, except where caused by authors' code.

Used by: WCAG-1.4.3, WCAG-1.4.6, WCAG-1.4.11 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-contrast-ratio>

<a id="dfn-correct-reading-sequence"></a>
### correct reading sequence

> any sequence where words and paragraphs are presented in an order that does not change the meaning of the content

Used by: WCAG-1.3.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-correct-reading-sequence>

<a id="dfn-css-pixels"></a>
### CSS pixel (key)

> visual angle of about 0.0213 degrees
>
> A CSS pixel is the canonical unit of measure for all lengths and measurements in CSS. This unit is density-independent, and distinct from actual hardware pixels present in a display. User agents and operating systems should ensure that a CSS pixel is set as closely as possible to the CSS Values and Units Module Level 3 reference pixel [css3-values], which takes into account the physical dimensions of the display and the assumed viewing distance (factors that cannot be determined by content authors).

Used by: WCAG-1.4.10, WCAG-2.4.13, WCAG-2.5.5, WCAG-2.5.8 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-css-pixels>

<a id="dfn-down-event"></a>
### down-event (key)

> platform event that occurs when the trigger stimulus of a pointer is depressed
>
> The down-event may have different names on different platforms, such as "touchstart" or "mousedown".

Used by: WCAG-2.5.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-down-event>

<a id="dfn-dragging-movements"></a>
### dragging movement (key) — new in 2.2

> an operation where the pointer engages with an element on the down-event and the element (or a representation of its position) follows the pointer until an up-event
>
> *Note:* Examples of draggable elements include list items, text elements, and images.

Used by: WCAG-2.5.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-dragging-movements>

<a id="dfn-emergency"></a>
### emergency

> a sudden, unexpected situation or occurrence that requires immediate action to preserve health, safety, or property

Used by: WCAG-2.2.4 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-emergency>

<a id="dfn-essential"></a>
### essential (key)

> if removed, would fundamentally change the information or functionality of the content, **and** information and functionality cannot be achieved in another way that would conform

Used by: WCAG-1.3.4, WCAG-1.4.5, WCAG-1.4.9, WCAG-1.4.11, WCAG-2.2.1, WCAG-2.2.2, WCAG-2.2.3, WCAG-2.3.3, WCAG-2.5.1, WCAG-2.5.2, WCAG-2.5.4, WCAG-2.5.5, WCAG-2.5.6, WCAG-2.5.7, WCAG-2.5.8, WCAG-3.3.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-essential>

<a id="dfn-extended-audio-description"></a>
### extended audio description

> audio description that is added to an audiovisual presentation by pausing the video so that there is time to add additional description
>
> *Note:* This technique is only used when the sense of the video would be lost without the additional audio description and the pauses between dialogue/narration are too short.

Used by: WCAG-1.2.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-extended-audio-description>

<a id="dfn-flashes"></a>
### flash

> a pair of opposing changes in relative luminance that can cause seizures in some people if it is large enough and in the right frequency range
>
> *Note 1:* See general flash and red flash thresholds for information about types of flash that are not allowed.
>
> *Note 2:* See also blinking.

Used by: WCAG-2.3.1, WCAG-2.3.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-flashes>

<a id="dfn-focus-indicator"></a>
### focus indicator (key) — new in 2.2

> pixels that are changed to visually indicate when a user interface component is in a focused state

Used by: WCAG-2.4.7, WCAG-2.4.13 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-focus-indicator>

<a id="dfn-functionality"></a>
### functionality

> processes and outcomes achievable through user action

Used by: WCAG-2.1.1, WCAG-2.1.3, WCAG-2.5.1, WCAG-2.5.2, WCAG-2.5.4, WCAG-2.5.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-functionality>

<a id="dfn-general-flash-and-red-flash-thresholds"></a>
### general flash and red flash thresholds (key)

> a flash or rapidly changing image sequence is below the threshold (i.e., content **passes**) if any of the following are true:
>
> - there are no more than three **general flashes** and / or no more than three **red flashes** within any one-second period; or
> - the combined area of flashes occurring concurrently occupies no more than a total of .006 steradians within any 10 degree visual field on the screen (25% of any 10 degree visual field on the screen) at typical viewing distance
>
> where:
>
> - A **general flash** is defined as a pair of opposing changes in relative luminance of 10% or more of the maximum relative luminance (1.0) where the relative luminance of the darker image is below 0.80; and where "a pair of opposing changes" is an increase followed by a decrease, or a decrease followed by an increase, and
> - A **red flash** is defined as any pair of opposing transitions involving a saturated red
>
> *Exception:* Flashing that is a fine, balanced, pattern such as white noise or an alternating checkerboard pattern with "squares" smaller than 0.1 degree (of visual field at typical viewing distance) on a side does not violate the thresholds.
>
> *Note 1:* For general software or web content, using a 341 x 256 pixel rectangle anywhere on the displayed screen area when the content is viewed at 1024 x 768 pixels will provide a good estimate of a 10 degree visual field for standard screen sizes and viewing distances (e.g., 15-17 inch screen at 22-26 inches). This resolution of 75 - 85 ppi is known to be lower, and thus more conservative than the nominal CSS pixel resolution of 96 ppi in CSS specifications. Higher resolutions displays showing the same rendering of the content yield smaller and safer images so it is lower resolutions that are used to define the thresholds.
>
> *Note 2:* A transition is the change in relative luminance (or relative luminance/color for red flashing) between adjacent peaks and valleys in a plot of relative luminance (or relative luminance/color for red flashing) measurement against time. A flash consists of two opposing transitions.
>
> *Note 3:* The new working definition in the field for **"pair of opposing transitions involving a saturated red"** (from WCAG 2.2) is a pair of opposing transitions where, one transition is either to or from a state with a value R/(R + G + B) that is greater than or equal to 0.8, and the difference between states is more than 0.2 (unitless) in the CIE 1976 UCS chromaticity diagram. [ISO_9241-391]
>
> *Note 4:* Tools are available that will carry out analysis from video screen capture. However, no tool is necessary to evaluate for this condition if flashing is less than or equal to 3 flashes in any one second. Content automatically passes (see #1 and #2 above).

Used by: WCAG-2.3.1 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-general-flash-and-red-flash-thresholds>

<a id="dfn-human-language-s"></a>
### human language

> language that is spoken, written or signed (through visual or tactile means) to communicate with humans
>
> *Note:* See also sign language.

Used by: WCAG-1.4.12, WCAG-3.1.1, WCAG-3.1.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-human-language-s>

<a id="dfn-idioms"></a>
### idiom

> phrase whose meaning cannot be deduced from the meaning of the individual words and the specific words cannot be changed without losing the meaning
>
> *Note:* Idioms cannot be translated directly, word for word, without losing their (cultural or language-dependent) meaning.
>
> *Example 1:* In English, "spilling the beans" means "revealing a secret." However, "knocking over the beans" or "spilling the vegetables" does not mean the same thing.
>
> *Example 2:* In Japanese, the phrase "さじを投げる" literally translates into "he throws a spoon," but it means that there is nothing he can do and finally he gives up.
>
> *Example 3:* In Dutch, "Hij ging met de kippen op stok" literally translates into "He went to roost with the chickens," but it means that he went to bed early.

Used by: WCAG-3.1.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-idioms>

<a id="dfn-images-of-text"></a>
### image of text (key)

> text that has been rendered in a non-text form (e.g., an image) in order to achieve a particular visual effect
>
> *Note:* This does not include text that is part of a picture that contains significant other visual content.
>
> *Example:* A person's name on a nametag in a photograph.

Used by: WCAG-1.4.3, WCAG-1.4.4, WCAG-1.4.5, WCAG-1.4.6, WCAG-1.4.9, WCAG-2.5.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-images-of-text>

<a id="dfn-informative"></a>
### informative

> for information purposes and not required for conformance
>
> *Note:* Content required for conformance is referred to as "normative."

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-informative>

<a id="dfn-input-error"></a>
### input error (key)

> information provided by the user that is not accepted
>
> *Note:* This includes:
>
> 1. Information that is required by the web page but omitted by the user
> 2. Information that is provided by the user but that falls outside the required data format or values

Used by: WCAG-1.4.13, WCAG-3.3.1, WCAG-3.3.3, WCAG-3.3.4, WCAG-3.3.6 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-input-error>

<a id="dfn-jargon"></a>
### jargon

> words used in a particular way by people in a particular field
>
> *Example:* The word StickyKeys is jargon from the field of assistive technology/accessibility.

Used by: WCAG-3.1.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-jargon>

<a id="dfn-keyboard-interface"></a>
### keyboard interface (key)

> interface used by software to obtain keystroke input
>
> *Note 1:* A keyboard interface allows users to provide keystroke input to programs even if the native technology does not contain a keyboard.
>
> *Example:* A touchscreen PDA has a keyboard interface built into its operating system as well as a connector for external keyboards. Applications on the PDA can use the interface to obtain keyboard input either from an external keyboard or from other applications that provide simulated keyboard output, such as handwriting interpreters or speech-to-text applications with "keyboard emulation" functionality.
>
> *Note 2:* Operation of the application (or parts of the application) through a keyboard-operated mouse emulator, such as MouseKeys, does not qualify as operation through a keyboard interface because operation of the program is through its pointing device interface, not through its keyboard interface.

Used by: WCAG-2.1.1, WCAG-2.1.2, WCAG-2.1.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-keyboard-interface>

<a id="dfn-keyboard-shortcuts"></a>
### keyboard shortcut (key)

> alternative means of triggering an action by the pressing of one or more keys

Used by: WCAG-2.1.4 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-keyboard-shortcuts>

<a id="dfn-labels"></a>
### label (key)

> text or other component with a text alternative that is presented to a user to identify a component within web content
>
> *Note 1:* A label is presented to all users whereas the name may be hidden and only exposed by assistive technology. In many (but not all) cases the name and the label are the same.
>
> *Note 2:* The term label is not limited to the label element in HTML.

Used by: WCAG-2.4.6, WCAG-2.5.3, WCAG-3.3.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-labels>

<a id="dfn-large-scale"></a>
### large scale (text) (key)

> with at least 18 point or 14 point bold or font size that would yield equivalent size for Chinese, Japanese and Korean (CJK) fonts
>
> *Note 1:* Fonts with extraordinarily thin strokes or unusual features and characteristics that reduce the familiarity of their letter forms are harder to read, especially at lower contrast levels.
>
> *Note 2:* Font size is the size when the content is delivered. It does not include resizing that may be done by a user.
>
> *Note 3:* The actual size of the character that a user sees is dependent both on the author-defined size and the user's display or user agent settings. For many mainstream body text fonts, 14 and 18 point is roughly equivalent to 1.2 and 1.5 em or to 120% or 150% of the default size for body text (assuming that the body font is 100%), but authors would need to check this for the particular fonts in use. When fonts are defined in relative units, the actual point size is calculated by the user agent for display. The point size should be obtained from the user agent, or calculated based on font metrics as the user agent does, when evaluating this success criterion. Users who have low vision would be responsible for choosing appropriate settings.
>
> *Note 4:* When using text without specifying the font size, the smallest font size used on major browsers for unspecified text would be a reasonable size to assume for the font. If a level 1 heading is rendered in 14pt bold or higher on major browsers, then it would be reasonable to assume it is large text. Relative scaling can be calculated from the default sizes in a similar fashion.
>
> *Note 5:* The 18 and 14 point sizes for roman texts are taken from the minimum size for large print (14pt) and the larger standard font size (18pt). For other fonts such as CJK languages, the "equivalent" sizes would be the minimum large print size used for those languages and the next larger standard large print size.

Used by: WCAG-1.4.3, WCAG-1.4.6 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-large-scale>

<a id="dfn-legal-commitments"></a>
### legal commitments (key)

> transactions where the person incurs a legally binding obligation or benefit
>
> *Example:* A marriage license, a stock trade (financial and legal), a will, a loan, adoption, signing up for the army, a contract of any type, etc.

Used by: WCAG-3.3.4 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-legal-commitments>

<a id="dfn-purpose-of-each-link"></a>
### link purpose (key)

> nature of the result obtained by activating a hyperlink

Used by: WCAG-2.4.4, WCAG-2.4.9 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-purpose-of-each-link>

<a id="dfn-live"></a>
### live (key)

> information captured from a real-world event and transmitted to the receiver with no more than a broadcast delay
>
> *Note 1:* A broadcast delay is a short (usually automated) delay, for example used in order to give the broadcaster time to cue or censor the audio (or video) feed, but not sufficient to allow significant editing.
>
> *Note 2:* If information is completely computer generated, it is not live.

Used by: WCAG-1.2.4, WCAG-1.2.9 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-live>

<a id="dfn-lower-secondary-education-level"></a>
### lower secondary education level

> the two or three year period of education that begins after completion of six years of school and ends nine years after the beginning of primary education
>
> *Note:* This definition is based on the International Standard Classification of Education [UNESCO].

Used by: WCAG-3.1.5 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-lower-secondary-education-level>

<a id="dfn-mechanism"></a>
### mechanism (key)

> process or technique for achieving a result
>
> *Note 1:* The mechanism may be explicitly provided in the content, or may be relied upon to be provided by either the platform or by user agents, including assistive technologies.
>
> *Note 2:* The mechanism needs to meet all success criteria for the conformance level claimed.

Used by: WCAG-1.4.2, WCAG-1.4.8, WCAG-1.4.13, WCAG-2.1.4, WCAG-2.2.2, WCAG-2.4.1, WCAG-2.4.9, WCAG-2.5.2, WCAG-3.1.3, WCAG-3.1.4, WCAG-3.1.6, WCAG-3.2.5, WCAG-3.2.6, WCAG-3.3.4, WCAG-3.3.6, WCAG-3.3.8, WCAG-3.3.9 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-mechanism>

<a id="dfn-media-alternative-for-text"></a>
### media alternative for text (key)

> media that presents no more information than is already presented in text (directly or via text alternatives)
>
> *Note:* A media alternative for text is provided for those who benefit from alternate representations of text. Media alternatives for text may be audio-only, video-only (including sign-language video), or audio-video.

Used by: WCAG-1.2.1, WCAG-1.2.2, WCAG-1.2.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-media-alternative-for-text>

<a id="dfn-motion-animation"></a>
### motion animation

> addition of steps between conditions to create the illusion of movement or to give a sense of a smooth transition
>
> *Example:* For example, an element which moves into place or changes size while appearing is considered to be animated. An element which appears instantly without transitioning is not using animation. Motion animation does not include changes of color, blurring, or opacity which do not change the perceived size, shape, or position of the element.

Used by: WCAG-2.3.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-motion-animation>

<a id="dfn-bounding-boxes"></a>
### minimum bounding box (key) — new in 2.2

> the smallest enclosing rectangle aligned to the horizontal axis within which all the points of a shape lie. For components which wrap onto multiple lines as part of a sentence or block of text (such as hypertext links), the bounding box is based on how the component would appear on a single line.

Used by: WCAG-2.5.8 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-bounding-boxes>

<a id="dfn-name"></a>
### name (key)

> text by which software can identify a component within web content to the user
>
> *Note 1:* The name may be hidden and only exposed by assistive technology, whereas a label is presented to all users. In many (but not all) cases, the label and the name are the same.
>
> *Note 2:* This is unrelated to the name attribute in HTML.

Used by: WCAG-1.1.1, WCAG-2.5.3, WCAG-4.1.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-name>

<a id="dfn-navigated-sequentially"></a>
### navigated sequentially

> navigated in the order defined for advancing focus (from one element to the next) using a keyboard interface

Used by: WCAG-2.4.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-navigated-sequentially>

<a id="dfn-non-text-content"></a>
### non-text content (key)

> any content that is not a sequence of characters that can be programmatically determined or where the sequence is not expressing something in human language
>
> *Note:* This includes ASCII art (which is a pattern of characters), emoticons, leetspeak (which uses character substitution), and images representing text

Used by: WCAG-1.1.1, WCAG-3.3.8 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-non-text-content>

<a id="dfn-normative"></a>
### normative

> required for conformance
>
> *Note 1:* One may conform in a variety of well-defined ways to this document.
>
> *Note 2:* Content identified as "informative" or "non-normative" is never required for conformance.

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-normative>

<a id="dfn-on-a-full-screen-window"></a>
### on a full-screen window (key)

> on the most common sized desktop/laptop display with the viewport maximized
>
> *Note:* Since people generally keep their computers for several years, it is best not to rely on the latest desktop/laptop display resolutions but to consider the common desktop/laptop display resolutions over the course of several years when making this evaluation.

Used by: WCAG-1.4.8 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-on-a-full-screen-window>

<a id="dfn-pause"></a>
### paused

> stopped by user request and not resumed until requested by user

Used by: WCAG-1.4.2, WCAG-2.2.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-pause>

<a id="dfn-perimeter"></a>
### perimeter (key) — new in 2.2

> continuous line forming the boundary of a shape not including shared pixels, or the minimum bounding box, whichever is shortest.
>
> *Example:* The perimeter calculation for a 2 CSS pixel perimeter around a rectangle is 4*h*+4*w*, where *h* is the height and *w* is the width. For a 2 CSS pixel perimeter around a circle it is 4𝜋*r*.

Used by: WCAG-2.4.13 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-perimeter>

<a id="dfn-pointer-inputs"></a>
### pointer input (key)

> input from a device that can target a specific coordinate (or set of coordinates) on a screen, such as a mouse, pen, or touch contact
>
> *Note:* See the Pointer Events definition for "pointer" [pointerevents].

Used by: WCAG-2.5.5, WCAG-2.5.8 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-pointer-inputs>

<a id="dfn-prerecorded"></a>
### prerecorded (key)

> information that is not live

Used by: WCAG-1.2.1, WCAG-1.2.2, WCAG-1.2.3, WCAG-1.2.5, WCAG-1.2.6, WCAG-1.2.7, WCAG-1.2.8, WCAG-1.4.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-prerecorded>

<a id="dfn-presentation"></a>
### presentation

> rendering of the content in a form to be perceived by users

Used by: WCAG-1.3.1, WCAG-1.4.11, WCAG-2.4.13, WCAG-2.5.5, WCAG-2.5.8 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-presentation>

<a id="dfn-primary-education"></a>
### primary education level

> six year time period that begins between the ages of five and seven, possibly without any previous education
>
> *Note:* This definition is based on the International Standard Classification of Education [UNESCO].

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-primary-education>

<a id="dfn-processes"></a>
### process (key)

> series of user actions where each action is required in order to complete an activity
>
> *Example 1:* Successful use of a series of web pages on a shopping site requires users to view alternative products, prices and offers, select products, submit an order, provide shipping information and provide payment information.
>
> *Example 2:* An account registration page requires successful completion of a Turing test before the registration form can be accessed.

Used by: WCAG-2.4.5, WCAG-3.3.7, WCAG-3.3.8, WCAG-3.3.9 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-processes>

<a id="dfn-programmatically-determinable"></a>
### programmatically determined (programmatically determinable) (key)

> determined by software from author-supplied data provided in a way that different user agents, including assistive technologies, can extract and present this information to users in different modalities
>
> *Example 1:* Determined in a markup language from elements and attributes that are accessed directly by commonly available assistive technology.
>
> *Example 2:* Determined from technology-specific data structures in a non-markup language and exposed to assistive technology via an accessibility API that is supported by commonly available assistive technology.

Used by: WCAG-1.3.1, WCAG-1.3.2, WCAG-1.3.5, WCAG-1.3.6, WCAG-3.1.1, WCAG-3.1.2, WCAG-4.1.2, WCAG-4.1.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-programmatically-determinable>

<a id="dfn-programmatically-determined-link-context"></a>
### programmatically determined link context (key)

> additional information that can be programmatically determined from relationships with a link, combined with the link text, and presented to users in different modalities
>
> *Example:* In HTML, information that is programmatically determinable from a link in English includes text that is in the same paragraph, list item, or table cell as the link or in a table header cell that is associated with the table cell that contains the link.
>
> *Note:* Since screen readers interpret punctuation, they can also provide the context from the current sentence, when the focus is on a link in that sentence.

Used by: WCAG-2.4.4 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-programmatically-determined-link-context>

<a id="dfn-programmatically-set"></a>
### programmatically set

> set by software using methods that are supported by user agents, including assistive technologies

Used by: WCAG-4.1.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-programmatically-set>

<a id="dfn-pure-decoration"></a>
### pure decoration (key)

> serving only an aesthetic purpose, providing no information, and having no functionality
>
> *Note:* Text is only purely decorative if the words can be rearranged or substituted without changing their purpose.
>
> *Example:* The cover page of a dictionary has random words in very light text in the background.

Used by: WCAG-1.1.1, WCAG-1.4.3, WCAG-1.4.6, WCAG-1.4.9 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-pure-decoration>

<a id="dfn-real-time-events"></a>
### real-time event (key)

> event that a) occurs at the same time as the viewing and b) is not completely generated by the content
>
> *Example 1:* A Webcast of a live performance (occurs at the same time as the viewing and is not prerecorded).
>
> *Example 2:* An on-line auction with people bidding (occurs at the same time as the viewing).
>
> *Example 3:* Live humans interacting in a virtual world using avatars (is not completely generated by the content and occurs at the same time as the viewing).

Used by: WCAG-2.2.1, WCAG-2.2.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-real-time-events>

<a id="dfn-regions"></a>
### region

> perceivable, programmatically determined section of content
>
> *Note:* In HTML, any area designated with a landmark role would be a region.

Used by: WCAG-1.3.6 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-regions>

<a id="dfn-relationships"></a>
### relationships (key)

> meaningful associations between distinct pieces of content

Used by: WCAG-1.3.1 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-relationships>

<a id="dfn-relative-luminance"></a>
### relative luminance (key)

> the relative brightness of any point in a colorspace, normalized to 0 for darkest black and 1 for lightest white
>
> *Note 1:* For the sRGB colorspace, the relative luminance of a color is defined as L = 0.2126 * **R** + 0.7152 * **G** + 0.0722 * **B** where **R**, **G** and **B** are defined as:
>
> - if RsRGB <= 0.04045 then **R** = RsRGB/12.92 else **R** = ((RsRGB+0.055)/1.055) ^ 2.4
> - if GsRGB <= 0.04045 then **G** = GsRGB/12.92 else **G** = ((GsRGB+0.055)/1.055) ^ 2.4
> - if BsRGB <= 0.04045 then **B** = BsRGB/12.92 else **B** = ((BsRGB+0.055)/1.055) ^ 2.4
>
> and RsRGB, GsRGB, and BsRGB are defined as:
>
> - RsRGB = R8bit/255
> - GsRGB = G8bit/255
> - BsRGB = B8bit/255
>
> The "^" character is the exponentiation operator. (Formula taken from [SRGB].)
>
> *Note 2:* Before May 2021 the value of 0.04045 in the definition was different (0.03928). It was taken from an older version of the specification and has been updated. It has no practical effect on the calculations in the context of these guidelines.
>
> *Note 3:* Almost all systems used today to view web content assume sRGB encoding. Unless it is known that another color space will be used to process and display the content, authors should evaluate using sRGB colorspace. If using other color spaces, see Understanding Success Criterion 1.4.3.
>
> *Note 4:* If dithering occurs after delivery, then the source color value is used. For colors that are dithered at the source, the average values of the colors that are dithered should be used (average R, average G, and average B).
>
> *Note 5:* Tools are available that automatically do the calculations when testing contrast and flash.
>
> *Note 6:* A separate page giving the relative luminance definition using MathML to display the formulas is available.

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-relative-luminance>

<a id="dfn-relied-upon"></a>
### relied upon (technologies that are) (key)

> the content would not conform if that technology is turned off or is not supported

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-relied-upon>

<a id="dfn-role"></a>
### role (key)

> text or number by which software can identify the function of a component within Web content
>
> *Example:* A number that indicates whether an image functions as a hyperlink, command button, or check box.

Used by: WCAG-4.1.2, WCAG-4.1.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-role>

<a id="dfn-same-functionality"></a>
### same functionality (key)

> same result when used
>
> *Example:* A submit "search" button on one web page and a "find" button on another web page may both have a field to enter a term and list topics in the website related to the term submitted. In this case, they would have the same functionality but would not be labeled consistently.

Used by: WCAG-3.2.4 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-same-functionality>

<a id="dfn-same-relative-order"></a>
### same relative order (key)

> same position relative to other items
>
> *Note:* Items are considered to be in the same relative order even if other items are inserted or removed from the original order. For example, expanding navigation menus may insert an additional level of detail or a secondary navigation section may be inserted into the reading order.

Used by: WCAG-3.2.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-same-relative-order>

<a id="dfn-satisfies"></a>
### satisfies a success criterion (key)

> the success criterion does not evaluate to 'false' when applied to the page

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-satisfies>

<a id="dfn-section"></a>
### section (key)

> a self-contained portion of written content that deals with one or more related topics or thoughts
>
> *Note:* A section may consist of one or more paragraphs and include graphics, tables, lists and sub-sections.

Used by: WCAG-2.4.10 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-section>

<a id="dfn-set-of-web-pages"></a>
### set of web pages (key)

> collection of web pages that share a common purpose and that are created by the same author, group or organization
>
> *Example:* Examples include:
>
> - a publication which is split across multiple web pages, where each page contains one chapter or other significant section of the work. The publication is logically a single contiguous unit, and contains navigation features that enable access to the full set of pages.
> - an e-commerce website shows products in a set of web pages that all share the same navigation and identification. However, when progressing to the checkout process, the template changes; the navigation and other elements are removed, so the pages in that process are functionally and visually different. The checkout pages are not part of the set of product pages.
> - a blog on a sub-domain (e.g. blog.example.com) which has a different navigation and is authored by a distinct set of people from the pages on the primary domain (example.com).
>
> *Note:* Different language versions would be considered different sets of web pages.

Used by: WCAG-2.4.5, WCAG-2.4.8, WCAG-3.2.3, WCAG-3.2.4, WCAG-3.2.6 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-set-of-web-pages>

<a id="dfn-sign-language"></a>
### sign language

> a language using combinations of movements of the hands and arms, facial expressions, or body positions to convey meaning

Used by: no SC text links it directly (used in conformance or other definitions) · Spec: <https://www.w3.org/TR/WCAG22/#dfn-sign-language>

<a id="dfn-sign-language-interpretation"></a>
### sign language interpretation

> translation of one language, generally a spoken language, into a sign language
>
> *Note:* True sign languages are independent languages that are unrelated to the spoken language(s) of the same country or region.

Used by: WCAG-1.2.6 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-sign-language-interpretation>

<a id="dfn-single-pointer"></a>
### single pointer (key)

> an input modality that only targets a single point on the page/screen at a time – such as a mouse, single finger on a touch screen, or stylus.
>
> *Note:* Single pointer interactions include clicks, double clicks, taps, dragging motions, and single-finger swipe gestures. In contrast, multipoint interactions involve the use of two or more pointers at the same time, such as two-finger interactions on a touchscreen, or the simultaneous use of a mouse and stylus.

Used by: WCAG-2.5.1, WCAG-2.5.2, WCAG-2.5.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-single-pointer>

<a id="dfn-specific-sensory-experience"></a>
### specific sensory experience

> a sensory experience that is not purely decorative and does not primarily convey important information or perform a function
>
> *Example:* Examples include a performance of a flute solo, works of visual art etc.

Used by: WCAG-1.1.1 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-specific-sensory-experience>

<a id="dfn-states"></a>
### state (key)

> dynamic property expressing characteristics of a user interface component that may change in response to user action or automated processes
>
> States do not affect the nature of the component, but represent data associated with the component or user interaction possibilities. Examples include focus, hover, select, press, check, visited/unvisited, and expand/collapse.

Used by: WCAG-1.4.11, WCAG-4.1.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-states>

<a id="dfn-status-messages"></a>
### status message (key)

> change in content that is not a change of context, and that provides information to the user on the success or results of an action, on the waiting state of an application, on the progress of a process, or on the existence of errors

Used by: WCAG-4.1.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-status-messages>

<a id="dfn-structure"></a>
### structure (key)

> - The way the parts of a web page are organized in relation to each other; and
> - The way a collection of web pages is organized

Used by: WCAG-1.3.1 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-structure>

<a id="dfn-style-properties"></a>
### style property (key)

> property whose value determines the presentation (e.g. font, color, size, location, padding, volume, synthesized speech prosody) of content elements as they are rendered (e.g. onscreen, via loudspeaker, via braille display) by user agents
>
> Style properties can have several origins:
>
> - User agent default styles: The default style property values applied in the absence of any author or user styles. Some web content technologies specify a default rendering, others do not;
> - Author styles: Style property values that are set by the author as part of the content (e.g. in-line styles, author style sheets);
> - User styles: Style property values that are set by the user (e.g. via user agent interface settings, user style sheets)

Used by: WCAG-1.4.12 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-style-properties>

<a id="dfn-supplementary-content"></a>
### supplemental content

> additional content that illustrates or clarifies the primary content
>
> *Example 1:* An audio version of a web page.
>
> *Example 2:* An illustration of a complex process.
>
> *Example 3:* A paragraph summarizing the major outcomes and recommendations made in a research study.

Used by: WCAG-3.1.5 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-supplementary-content>

<a id="dfn-synchronized-media"></a>
### synchronized media (key)

> audio or video synchronized with another format for presenting information and/or with time-based interactive components, unless the media is a media alternative for text that is clearly labeled as such

Used by: WCAG-1.2.2, WCAG-1.2.3, WCAG-1.2.4, WCAG-1.2.5, WCAG-1.2.6, WCAG-1.2.7, WCAG-1.2.8, WCAG-2.2.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-synchronized-media>

<a id="dfn-targets"></a>
### target (key)

> region of the display that will accept a pointer action, such as the interactive area of a user interface component
>
> *Note:* If two or more targets are overlapping, the overlapping area should not be included in the measurement of the target size, except when the overlapping targets perform the same action or open the same page.

Used by: WCAG-2.5.5, WCAG-2.5.8 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-targets>

<a id="dfn-technologies"></a>
### technology (web content)

> mechanism for encoding instructions to be rendered, played or executed by user agents
>
> *Note 1:* As used in these guidelines "web technology" and the word "technology" (when used alone) both refer to web content technologies.
>
> *Note 2:* Web content technologies may include markup languages, data formats, or programming languages that authors may use alone or in combination to create end-user experiences that range from static web pages to synchronized media presentations to dynamic Web applications.
>
> *Example:* Some common examples of web content technologies include HTML, CSS, SVG, PNG, PDF, Flash, and JavaScript.

Used by: WCAG-2.4.13 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-technologies>

<a id="dfn-text"></a>
### text

> sequence of characters that can be programmatically determined, where the sequence is expressing something in human language

Used by: WCAG-1.1.1, WCAG-1.4.3, WCAG-1.4.4, WCAG-1.4.5, WCAG-1.4.6, WCAG-1.4.9, WCAG-1.4.12, WCAG-2.5.3, WCAG-3.1.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-text>

<a id="dfn-text-alternative"></a>
### text alternative (key)

> Text that is programmatically associated with non-text content or referred to from text that is programmatically associated with non-text content. Programmatically associated text is text whose location can be programmatically determined from the non-text content.
>
> *Example:* An image of a chart is described in text in the paragraph after the chart. The short text alternative for the chart indicates that a description follows.
>
> *Note:* Refer to Understanding Text Alternatives for more information.

Used by: WCAG-1.1.1 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-text-alternative>

<a id="dfn-up-event"></a>
### up-event (key)

> platform event that occurs when the trigger stimulus of a pointer is released
>
> The up-event may have different names on different platforms, such as "touchend" or "mouseup".

Used by: WCAG-2.5.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-up-event>

<a id="dfn-used-in-an-unusual-or-restricted-way"></a>
### used in an unusual or restricted way (key)

> words used in such a way that requires users to know exactly which definition to apply in order to understand the content correctly
>
> *Example:* The term "gig" means something different if it occurs in a discussion of music concerts than it does in article about computer hard drive space, but the appropriate definition can be determined from context. By contrast, the word "text" is used in a very specific way in WCAG 2, so a definition is supplied in the glossary.

Used by: WCAG-3.1.3 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-used-in-an-unusual-or-restricted-way>

<a id="dfn-user-agents"></a>
### user agent

> any software that retrieves and presents web content for users
>
> *Example:* Web browsers, media players, plug-ins, and other programs — including assistive technologies — that help in retrieving, rendering, and interacting with web content.

Used by: WCAG-1.4.11, WCAG-1.4.13, WCAG-2.4.13, WCAG-2.5.5, WCAG-2.5.7, WCAG-2.5.8, WCAG-4.1.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-user-agents>

<a id="dfn-user-controllable"></a>
### user-controllable

> data that is intended to be accessed by users
>
> *Note:* This does not refer to such things as Internet logs and search engine monitoring data.
>
> *Example:* Name and address fields for a user's account.

Used by: WCAG-3.3.4 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-user-controllable>

<a id="dfn-user-interface-components"></a>
### user interface component (key)

> a part of the content that is perceived by users as a single control for a distinct function
>
> *Note 1:* Multiple user interface components may be implemented as a single programmatic element. "Components" here is not tied to programming techniques, but rather to what the user perceives as separate controls.
>
> *Note 2:* User interface components include form elements and links as well as components generated by scripts.
>
> *Note 3:* What is meant by "component" or "user interface component" here is also sometimes called "user interface element".
>
> *Example:* An applet has a "control" that can be used to move through content by line or page or random access. Since each of these would need to have a name and be settable independently, they would each be a "user interface component."

Used by: WCAG-1.3.6, WCAG-1.4.3, WCAG-1.4.6, WCAG-1.4.11, WCAG-2.1.4, WCAG-2.4.10, WCAG-2.4.11, WCAG-2.4.12, WCAG-2.5.3, WCAG-2.5.4, WCAG-3.2.1, WCAG-3.2.2, WCAG-4.1.2 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-user-interface-components>

<a id="dfn-user-inactivity"></a>
### user inactivity (key)

> any continuous period of time where no user actions occur
>
> The method of tracking will be determined by the website or application.

Used by: WCAG-2.2.6 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-user-inactivity>

<a id="dfn-video"></a>
### video

> the technology of moving or sequenced pictures or images
>
> *Note:* Video can be made up of animated or photographic images, or both.

Used by: WCAG-1.2.3, WCAG-1.2.5, WCAG-1.2.7 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-video>

<a id="dfn-video-only"></a>
### video-only

> a time-based presentation that contains only video (no audio and no interaction)

Used by: WCAG-1.2.1, WCAG-1.2.8 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-video-only>

<a id="dfn-viewport"></a>
### viewport (key)

> object in which the user agent presents content
>
> *Note 1:* The user agent presents content through one or more viewports. Viewports include windows, frames, loudspeakers, and virtual magnifying glasses. A viewport may contain another viewport (e.g., nested frames). Interface components created by the user agent such as prompts, menus, and alerts are not viewports.
>
> *Note 2:* This definition is based on User Agent Accessibility Guidelines 1.0 Glossary [UAAG10].

Used by: WCAG-1.4.10 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-viewport>

<a id="dfn-visually-customized"></a>
### visually customized

> the font, size, color, and background can be set

Used by: WCAG-1.4.5 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-visually-customized>

<a id="dfn-web-page-s"></a>
### web page (key)

> a non-embedded resource obtained from a single URI using HTTP plus any other resources that are used in the rendering or intended to be rendered together with it by a user agent
>
> *Note 1:* Although any "other resources" would be rendered together with the primary resource, they would not necessarily be rendered simultaneously with each other.
>
> *Note 2:* For the purposes of conformance with these guidelines, a resource must be "non-embedded" within the scope of conformance to be considered a web page.
>
> *Example 1:* A web resource including all embedded images and media.
>
> *Example 2:* A web mail program built using Asynchronous JavaScript and XML (AJAX). The program lives entirely at http://example.com/mail, but includes an inbox, a contacts area and a calendar. Links or buttons are provided that cause the inbox, contacts, or calendar to display, but do not change the URI of the page as a whole.
>
> *Example 3:* A customizable portal site, where users can choose content to display from a set of different content modules.
>
> *Example 4:* When you enter "http://shopping.example.com/" in your browser, you enter a movie-like interactive shopping environment where you visually move around in a store dragging products off of the shelves around you and into a visual shopping cart in front of you. Clicking on a product causes it to be demonstrated with a specification sheet floating alongside. This might be a single-page website or just one page within a website.

Used by: WCAG-2.3.1, WCAG-2.3.2, WCAG-2.4.1, WCAG-2.4.2, WCAG-2.4.3, WCAG-2.4.5, WCAG-3.1.1, WCAG-3.2.3, WCAG-3.2.6, WCAG-3.3.4, WCAG-3.3.6 · Spec: <https://www.w3.org/TR/WCAG22/#dfn-web-page-s>
