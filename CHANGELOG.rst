.. _changelog:

<!-- version list -->

.. _changelog-v0.1.0:

v0.1.0 (2025-04-27)
===================

✨ Features
-----------

* Add debug mode support in build script and CI workflows (`257d597`_)

* Add logo.ico resource file (`785a60b`_)

* Add shared memory mechanism to prevent duplicate application instances (`93e2079`_)

* Add Tray Icon (`28b37e1`_)

* Basic i18n support (`4dcbeaf`_)

* Completely refactor the business logic, closes `#5`_ (`3486cd5`_)

* Completely refactoring the GUI with PySide6 and QFluentWidgets (`6572fda`_)

* Optimize tray menu (`576168a`_)

* Remove the searchWindowName config item and add the detectionMethods config item (`7ee40f2`_)

* **ci**: Add build script for project packaging and deployment (`9250f94`_)

* **ci**: Enhance build and release pipeline with multi-arch support (`b8270d5`_)

* **ci**: Make UPX compression configurable (`e3ec96b`_)

🪲 Bug Fixes
------------

* Handle deadlock during initialization of translations (`b9c70bd`_)

* Handle None values for default comboBox selection (`b3c9c2a`_)

* Icon path (`1775f13`_)

* Restrict Python version to >=3.12,<3.13 (`c4f075f`_)

* **ci**: Add Dependency Walker to setup step in CI and release workflows (`c900b7d`_)

* **ci**: Add UPX and 7-Zip installation to release workflow (`2fa07e9`_)

* **ci**: Correct artifact naming for debug builds (`d238f35`_)

* **ci**: Correct cache key format in GitHub Actions workflow (`b7bb79a`_)

* **ci**: Correct cache path (`63e9ab3`_)

* **ci**: Handle compatibility issues between CI and GitHub Actions (`054e597`_)

* **ci**: Switch release jobs to run on ubuntu-latest (`1f68c90`_)

* **ci**: Update build script to use PowerShell (*.ps1) (`6f4f3b7`_)

* **ci**: Update dependencies to include UPX and 7-Zip in CI setup (`b53a34b`_)

* **ci**: Update version handling in workflow and pyproject.toml (`7e5bcd8`_)

* **i18n**: Update line references (`491058a`_)

📖 Documentation
----------------

* Update README (`d31b0cd`_)

♻️ Refactoring
---------------

* Remove unnecessary blank lines in main.py (`614f3b5`_)

* Replace os.execl with QProcess for app restart and improve cleanup logic (`aacc3f4`_)

* **ci**: Restructure release and CI workflows with job modularization (`5a4e1ec`_)

* **ci**: Update debug matrix (`bb8130d`_)

* **i18n**: Update line references in translations for en_US, zh_CN, and ja_JP (`c80532d`_)

🤖 Continuous Integration
-------------------------

* Add a repository checkout step (`72d0c68`_)

* Add CI workflow for building and releasing artifacts (`684d385`_)

* Add continuous delivery workflow and release templates (`6e9fffc`_)

* Change release to manual trigger (`cd33301`_)

* Disable UPX compression by default (`634c083`_)

* Enable cross-OS caching (`7ff9809`_)

🧹 Chores
---------

* Add renovate.json (`8ada61b`_)

* Disable major version bump on version 0.x.x (`896c630`_)

* Remove old icon (`a869de2`_)

* Simplify .gitignore (`ac42388`_)

* Standardized project structure (`1524713`_)

* Switch to uv (`3a7ea94`_)

* **deps**: Bump dependencies (`9d94bb9`_)

* **deps**: Bump pyside6 and related packages to 6.9.0 (`3999e16`_)

* **deps**: Update astral-sh/setup-uv action to v6 (`PR#6`_, `0047c0d`_)

* **deps**: Update dependencies for Python, numpy, and pillow versions (`062f53a`_)

.. _#5: https://github.com/Illustar0/PowerToysRunEnhance/issues/5
.. _0047c0d: https://github.com/Illustar0/PowerToysRunEnhance/commit/0047c0dc2e32d25516365b0a340686efe0b1a35d
.. _054e597: https://github.com/Illustar0/PowerToysRunEnhance/commit/054e5977bfca2c2e5ae12354a76fa3c21751a4e3
.. _062f53a: https://github.com/Illustar0/PowerToysRunEnhance/commit/062f53a3afc18445f414371941be2fdc909447b4
.. _1524713: https://github.com/Illustar0/PowerToysRunEnhance/commit/1524713b48f74d7a4d4af5af842f536952317a46
.. _1775f13: https://github.com/Illustar0/PowerToysRunEnhance/commit/1775f138ab3fc3f5b7bbddf03ac90625f30c6f3c
.. _1f68c90: https://github.com/Illustar0/PowerToysRunEnhance/commit/1f68c90e23514beff54a9afbf3cac42b80014794
.. _257d597: https://github.com/Illustar0/PowerToysRunEnhance/commit/257d597a8272a909046489acc321dac4791679d1
.. _28b37e1: https://github.com/Illustar0/PowerToysRunEnhance/commit/28b37e1c0be34b934914285942ee3847f9586aca
.. _2fa07e9: https://github.com/Illustar0/PowerToysRunEnhance/commit/2fa07e91a484f3e87b2f627fd433ecaef3d2dd31
.. _3486cd5: https://github.com/Illustar0/PowerToysRunEnhance/commit/3486cd56b71a60aa24b5775997c4ac6578e5c4e7
.. _3999e16: https://github.com/Illustar0/PowerToysRunEnhance/commit/3999e168046b311594b1ea591554820db5ce4f2a
.. _3a7ea94: https://github.com/Illustar0/PowerToysRunEnhance/commit/3a7ea94cd3cceeefff8cc2a9f940461eb73f87a6
.. _491058a: https://github.com/Illustar0/PowerToysRunEnhance/commit/491058aee450b4497606f2f04b0f1b5a1de415cd
.. _4dcbeaf: https://github.com/Illustar0/PowerToysRunEnhance/commit/4dcbeaf7f64ecf3e3f07897a561b797f2aa123d5
.. _576168a: https://github.com/Illustar0/PowerToysRunEnhance/commit/576168a2484878daac11e6d71c981a5f562ed977
.. _5a4e1ec: https://github.com/Illustar0/PowerToysRunEnhance/commit/5a4e1ec19baf4912adffae62b4ef2fa2099d648c
.. _614f3b5: https://github.com/Illustar0/PowerToysRunEnhance/commit/614f3b5d9d735af14b5976f5dc6cd4ad6f078247
.. _634c083: https://github.com/Illustar0/PowerToysRunEnhance/commit/634c0832a393bfd7a69dd9c11bcedb3903c174d1
.. _63e9ab3: https://github.com/Illustar0/PowerToysRunEnhance/commit/63e9ab31317760555dda255c7cb3bee878358267
.. _6572fda: https://github.com/Illustar0/PowerToysRunEnhance/commit/6572fdade41fa09baee7d08e8ab80624b017a651
.. _684d385: https://github.com/Illustar0/PowerToysRunEnhance/commit/684d385045b9ed9a70b4c0c357d1c7924b7c948a
.. _6e9fffc: https://github.com/Illustar0/PowerToysRunEnhance/commit/6e9fffcf7f9f6f05828b6f57e56871a447948576
.. _6f4f3b7: https://github.com/Illustar0/PowerToysRunEnhance/commit/6f4f3b7d87b9ec75a563d095e340e7d6b6c3fbb5
.. _72d0c68: https://github.com/Illustar0/PowerToysRunEnhance/commit/72d0c680a20b40f0fe679333b98e1cc8abbb1b3e
.. _785a60b: https://github.com/Illustar0/PowerToysRunEnhance/commit/785a60be10e748b7384139769794292e2ba36e8b
.. _7e5bcd8: https://github.com/Illustar0/PowerToysRunEnhance/commit/7e5bcd8bb15d4044a76bd77b7d330d97a516e42d
.. _7ee40f2: https://github.com/Illustar0/PowerToysRunEnhance/commit/7ee40f2efe350ca82750183d362bfead1bc62d18
.. _7ff9809: https://github.com/Illustar0/PowerToysRunEnhance/commit/7ff9809631df329f623ce33554820b16693de749
.. _896c630: https://github.com/Illustar0/PowerToysRunEnhance/commit/896c630a4c56611827157a7c48a6728f1f98103f
.. _8ada61b: https://github.com/Illustar0/PowerToysRunEnhance/commit/8ada61bb24a55dee7bf7993285f80b36688646bb
.. _9250f94: https://github.com/Illustar0/PowerToysRunEnhance/commit/9250f94b43cf3c70e308e00c3f484e5ae60bc12f
.. _93e2079: https://github.com/Illustar0/PowerToysRunEnhance/commit/93e20798c6231120d3bc473f302ecdde29241bf5
.. _9d94bb9: https://github.com/Illustar0/PowerToysRunEnhance/commit/9d94bb966e0df129cdbca62d05a6764dddeb6c66
.. _a869de2: https://github.com/Illustar0/PowerToysRunEnhance/commit/a869de2a46eae894a68a62208ec0bd0655403040
.. _aacc3f4: https://github.com/Illustar0/PowerToysRunEnhance/commit/aacc3f4dbbeff8ef9706651f133bcceee8b8ec89
.. _ac42388: https://github.com/Illustar0/PowerToysRunEnhance/commit/ac42388b380bb9119e9231565497bb9c84b38b77
.. _b3c9c2a: https://github.com/Illustar0/PowerToysRunEnhance/commit/b3c9c2a9939ea2073e93ace62292618c47bb10fd
.. _b53a34b: https://github.com/Illustar0/PowerToysRunEnhance/commit/b53a34b4915d71a57328cb8169fbc73af5dec9c2
.. _b7bb79a: https://github.com/Illustar0/PowerToysRunEnhance/commit/b7bb79a3552b4ee08f4d4b690bf9d5715c9aa774
.. _b8270d5: https://github.com/Illustar0/PowerToysRunEnhance/commit/b8270d5be5d764df6d857481d31ffaa163e715cd
.. _b9c70bd: https://github.com/Illustar0/PowerToysRunEnhance/commit/b9c70bd58b0c2adb59d8c469868ffaeab1e1f64a
.. _bb8130d: https://github.com/Illustar0/PowerToysRunEnhance/commit/bb8130d4e0b9bcfdc363c97a6c980d1d24257a06
.. _c4f075f: https://github.com/Illustar0/PowerToysRunEnhance/commit/c4f075f2c313cee3401548924ce5a21b34a445ae
.. _c80532d: https://github.com/Illustar0/PowerToysRunEnhance/commit/c80532de579ebbd95c681c4d8b741bb6c7bf73a4
.. _c900b7d: https://github.com/Illustar0/PowerToysRunEnhance/commit/c900b7d7c326c4e91e15d5f2efe3037a3b7e97cf
.. _cd33301: https://github.com/Illustar0/PowerToysRunEnhance/commit/cd333017648efc6c8968f7bdd6c400af82e8e526
.. _d238f35: https://github.com/Illustar0/PowerToysRunEnhance/commit/d238f3526d6232d5b9a11bad218580608ed2dfcf
.. _d31b0cd: https://github.com/Illustar0/PowerToysRunEnhance/commit/d31b0cdacc0549502a91c1cf52d799bbbd6a09db
.. _e3ec96b: https://github.com/Illustar0/PowerToysRunEnhance/commit/e3ec96ba7addbdbf516cc769df16a9f6cc6f9128
.. _PR#6: https://github.com/Illustar0/PowerToysRunEnhance/pull/6


.. _changelog-v0.0.1:

v0.0.1 (2024-11-12)
===================

* Initial Release
