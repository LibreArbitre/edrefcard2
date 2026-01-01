# Change Log

## 2.0.1 (2025-12-31)
### Bug Fixes
* **Template Error**: Fixed Jinja2 TemplateSyntaxError in `refcard.html` that caused 500 errors on configuration pages
* **Data Migration**: Fixed auto-migration to handle partial database states (88 configs successfully restored)
* **Error Handling**: Fixed `Config.path` method call error in Admin module that caused 500 errors
* **CI/CD**: Resolved ruff linting failures by updating configuration (748 → 30 errors, 96% reduction)

### Features
* **Lightbox**: Added full-screen image viewer for reference cards
  - Click-to-zoom on any reference card image
  - Close with X button or Escape key
  - Smooth animations and responsive design
* **Docker Testing**: Added automated Docker build and startup tests to CI pipeline

### Improvements
* **Python Version**: Upgraded to Python 3.13 for better performance and longer support
  - Updated base Docker image to `python:3.13-slim`
  - CI now tests Python 3.12, 3.13, and 3.14
  - Support lifecycle extended until October 2029
* **Code Quality**: Updated ruff and mypy configurations for modern Python
* **Documentation**: Updated README with current Python requirements and features

## 2.0.0 (2025-12-31)
### Major Features
* **Admin Panel**: Introduced a secured Admin Dashboard (`/admin`) for managing configurations and devices.
* **SQLite Database**: Migrated from file-based storage (Pickle) to a structured SQLite database for better performance and data integrity.
* **Docker Support**: Added `Dockerfile` and `docker-compose.yaml` for streamlined deployment and development.
* **Authentication**: Implemented HTTP Basic Auth for admin routes.

### Improvements
* **Architecture**: Refactored into Flask Blueprints for better modularity.
* **CI/CD**: Added GitHub Actions workflows for automated testing and linting.
* **Code Quality**: Integrated `ruff` for code style enforcement.
* **Modernization**: Updated dependencies and removed legacy code.

## 1.4
  * Completed all the outstanding pull requests from GitHub and merged them
  * Adjusted for Python 3.10 compatibility
  * Tested with Python 3.10/Ubuntu 22.04 on WSL2
  * Added support for Xbox360 controller clone (VOYEE Wired 360 - HY4102)

## 1.3.1
* Sundry cleanup and fixes.

## 1.3
* Added support for VKB Gladiator Left and Right sticks, courtesy of awerschlan and esabouraud.
* Added support for VPC Alpha Left and Right grips, courtesy of Slion.
* Added searching by controller type, courtesy of alewando.
* Added support for Odyssey's "On Foot" bindings.

## 1.2.8
* Added support for VKB Kosmosima SCG Left and Right grips, courtesy of ajhewett.
* Handled invalid keyboard bindings of the form `Device="Keyboard" Key=""`

## 1.2.7
* Added support for Thrustmaster Hotas Cougar.

## 1.2.6
* Added binding for Store Toggle Preview.

## 1.2.5
* Added bindings for the Store Camera.
* Revised the color palette.

## 1.2.4

* Amended the VKB Gladiator bindings: my thanks to KellyR (CMDR Analee Winston) for kicking my behind on this an providing corroborating data.
* Added a new URL `https://edrefcard/devices` listing all supported devices by primary name and linking to:
  * New endpoints `https://edrefcard//device/xxx` that show the given device's button names in rectangles shaded in light green and outlined in red, to assist with (a) debugging button mappings and (b) aligning the rectangles pixel-perfect.
* Tweaked CSS styling and column width settings for `/list` and `/devices` to make the table neater. I'll be the first to admit this isn't my strong suit.
* Reduced the maximum input length for the "description" field to 190 characters in light of the above.
* Updated the forum thread URL.

## 1.2.3

* Restored caching of rendered JPEGs to one day now that we have more disk space.

## 1.2.2

* Improved the error reporting when there is an error parsing the bindings file.

## 1.2.1

* Added the new bindings introduced in Chapter 4 beta 3.
* Updated the code that prevents redundant specialisations from being shown on the same card (e.g. when GalMap pitch axis is the same as your regular pitch axis). This should make cards more concise w/o loss of clarity.

## 1.2

* Command names are now in Title Case and some have been abbreviated.
* The keyboard chart makes more use of symbols to identify the keys.
* The Galaxy map controls now say "GalMap" rather than "Camera".
* Added support for Dual Virpil VPC WarBRD DELTA joysticks.
* Added support for Saitek X45 HOTAS.

## 1.1

* Blocking "spammy" descriptions is as those starting with punctuation.

## 1.0.8

* Added bindings introduced in Chapter 4, notable the FSS scanner.

## 1.0.7

* Fixed errors with non-ASCII file encodings. Should now be fully Unicode.

## 1.0.6

* The list view is now sorted in a case-insensitive manner.
* The home page now correctly uses https to access its style sheet from Google APIs. Thanks to eeisenhart.

