# Community reply drafts October 3 2026

Ready-to-edit replies for the public thread and the two private conversations.
They describe work in progress, not released support. None has been sent.
Keep each reply attached to its relevant post rather than posting all replies as
one large announcement.

## Public progress update

Hi everyone, and apologies for the slow replies. I'm back working on EDRefCard2
and have reviewed the recent controller requests and the files you shared.

The editor already has quite a few features, but I want to be honest: adding a
controller is not yet as straightforward as I initially hoped. I'm now focusing
on making the whole process reliable, especially imported reference sheets,
button groups, axis directions and checking the result against real bindings.

The aim is a reusable controller template, not a card tied to one person's
mapping. You don't need to bind every button or change your normal setup to help.
Your usual .binds file, the exact controller variant and confirmation that the
actions appear beside the correct physical controls are very useful.

Thanks again for the files, screenshots and offers to test. I'll share previews
for validation before announcing support as available. For uploads and testing,
please use https://beta.edrefcard.info/; the original live site is separate.

## Alicina public post

Thanks for the report, and for the pedal details you sent privately. I already
have your iapcqr bindings reference, so there is no need to upload it again.

I also need to correct my earlier explanation about TARGET. Your file contains
the physical Warthog stick and throttle, not a combined TARGET device. The
warning is a false positive in the detection logic, not evidence that TARGET is
still running or that you need to edit your bindings. I'm correcting that in
the refactored beta; it won't automatically change the separate original live
site.

For the Orion pedals, I now have the hardware ID and the three axis codes.
I've prepared a draft on staging and checked it against your existing bindings.
I'll share the preview once the visual review is complete.

## Alicina private message

Hi Alicina,

Thanks, I have the screenshots you sent by email and your axis confirmation.
That gives me the missing information: device ID 4098BEF0, yaw on Joy_RZAxis,
right toe brake on Joy_RXAxis and left toe brake on Joy_RYAxis.

I already have your iapcqr .binds reference, so you don't need to send it again
or assign anything extra. Your current profile only uses yaw, but the template
will also include both brake axes for people who bind them.

I've also checked the TARGET warning properly. My earlier explanation was
wrong: your file does not contain a combined TARGET device. It's a detection
bug, and you don't need to change your setup. I'm correcting it in the beta
codebase, which is separate from the original live site.

I've now prepared the Orion draft and checked it against your existing profile.
Both unused brake groups stay hidden on your card, while the template includes
them for other users. I'll send the preview after the visual review so you can
check it against your pedals.
You won't need to learn the editor; confirming the physical left/right labels
and the placement of your actions will be the useful part.

Thanks again for helping!

## TyWuNon private message

Hi,

Sorry about that! You can email the .binds file, screenshots and product link
to librearbitre67@gmail.com. If you prefer, upload your .binds to
https://beta.edrefcard.info/, untick the option to list it in the public
catalogue, and send me the resulting reference. An unlisted card is still
accessible to anyone who has its link, so email is the better option if you
don't want to share it that way.

Please use your normal bindings; there's no need to assign every input. The
exact Mini Left-Hand variant, any extra modules, and a VKBDevCfg screenshot
showing its name and VID/PID would help me avoid confusing it with the Max
configuration another owner has shared.

I'll prepare a draft and a preview for you to check. You won't need to learn
the editor unless you would like to.

Thanks for offering to help!

## SansFrontieres public reply

Thank you, this is exactly the sort of evidence I needed. I can access the new
.binds file and the five VKBDevCfg screenshots.

I've noted the two IDs: 231D0125 for your Gunfighter MCG Ultimate XT2, and
231D0139 for your STECS Space-L Max with STEM. Since you've customized the
configuration, I'll compare the input assignments with the screenshots rather
than assuming an existing STECS template uses the same numbering.

No need to change your bindings. The next useful step will be checking a
preview against your hardware once I've prepared it. Thanks again!

## Zach Drachenherz public reply

Thanks for tracking down the source! I found the editable Google Drawing linked
from the Reddit post. I'll check with the original author about adapting it
and keeping the credit if we use the artwork.

One detail matters for integration: the original author mentions using both
sticks in right-hand mode, so I can't assume the drawing confirms the default
left/right input numbering in Elite. Your usual .binds file and confirmation
of the mode switch positions would still be helpful whenever you have time.
You don't need to bind anything extra.

## Martyn Skytech public reply

Thanks for the report and the official PDF links. I can access your attached
bindings file. The game records device IDs 10F57150 and 10F57154 in that file,
which differ from the identifiers you quoted, so I'll use the .binds values
for detection.

The reference PDFs are genuinely fillable, but their field format differs
from the sheets the importer currently supports. They are useful source
material; they need a dedicated importer adaptation rather than simply
being uploaded unchanged.

Could you confirm which of those two game IDs belongs to the Flightstick II
and which to the Dual Throttle? A Windows or Turtle Beach configuration
screenshot showing the device identity would help if available. You don't
need to recreate your bindings.

## RahmBro public reply

Thanks, I can access your bindings file and have noted 334440CC for your WarBRD
base with ALPHA R grip, and 33440194 for your T-50CM3 throttle.

These may be new IDs for hardware we can already represent, but I'll compare
the button and axis assignments before attaching them to an existing template.
A changed ID doesn't always mean a changed mapping, and I don't want to make
your device appear supported with actions beside the wrong controls.

If you have customized the logical button assignments in VPC Software,
screenshots of those assignments would be helpful. Otherwise, I'll start with
the manufacturer sheets and your current file. Thanks for sharing them!
