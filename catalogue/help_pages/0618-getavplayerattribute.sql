INSERT INTO "help_pages" ("id", "url", "locale", "kind", "fetched_at", "http_status", "page_modified_at", "raw_html", "sha256") VALUES (618, 'https://help.claris.com/en/pro-help/content/getavplayerattribute.html', 'en', 'function', '2026-10-07T22:16:33Z', 200, '2024-06-04T08:10-07:00', '<!DOCTYPE html>
<html xmlns:MadCap="http://www.madcapsoftware.com/Schemas/MadCap.xsd" lang="en-us" xml:lang="en-us" class="_Skins_Claris_SideNav_HTML5" data-mc-search-type="Stem" data-mc-help-system-file-name="index.xml" data-mc-path-to-help-system="../" data-mc-has-content-body="True" data-mc-toc-path="[%=doc-specific-variables.reference-title%]|[%=System.LinkedTitle%]|[%=System.LinkedTitle%]" data-mc-target-type="WebHelp2" data-mc-runtime-file-type="Topic;Default" data-mc-preload-images="false" data-mc-in-preview-mode="false">
    <head>
        <meta property="article:modified_time" content="2024-06-04T08:10-07:00" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta charset="utf-8" />
        <meta name="docID" content="pro-help" />
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><title>GetAVPlayerAttribute</title>
        <link rel="canonical" href="https://help.claris.com/en/pro-help/content/getavplayerattribute.html" />
        <link href="../Skins/Default/Stylesheets/Slideshow.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Default/Stylesheets/TextEffects.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Default/Stylesheets/Topic.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Default/Stylesheets/Components/Styles.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Default/Stylesheets/Components/Tablet.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Default/Stylesheets/Components/Mobile.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Default/Stylesheets/Components/Print.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Fluid/stylesheets/foundation.6.2.3.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Fluid/stylesheets/styles.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Fluid/stylesheets/tablet.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Fluid/stylesheets/mobile.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="../Skins/Fluid/stylesheets/print.css" rel="stylesheet" type="text/css" data-mc-generated="True" />
        <link href="/assets/css/header-styles.css" rel="stylesheet" type="text/css" />
        <link href="/assets/css/footer-styles.css" rel="stylesheet" type="text/css" />
        <style>/*&lt;meta /&gt;*/

.button.remove-highlight-button
{
	-pie-background: linear-gradient(transparent, transparent);
}

.button.copy-as-markdown-button
{
	-pie-background: linear-gradient(transparent, transparent);
}

.button.previous-topic-button
{
	-pie-background: linear-gradient(transparent, transparent);
}

.button.print-button
{
	-pie-background: linear-gradient(transparent, transparent);
}

.button.next-topic-button
{
	-pie-background: linear-gradient(transparent, transparent);
}

.needs-pie
{
	behavior: url(''../Resources/Scripts/PIE-no-motw.htc'');
}

</style>
        <link href="resources/stylesheets/styles.css" rel="stylesheet" type="text/css" />
        <link href="resources/tablestyles/standardtable.css" rel="stylesheet" data-mc-stylesheet-type="table" />
        <script src="../Resources/Scripts/jquery.min.js" type="text/javascript">
        </script>
        <script src="../Resources/Scripts/purify.min.js" type="text/javascript" defer="defer">
        </script>
        <script src="../Resources/Scripts/require.min.js" type="text/javascript" defer="defer">
        </script>
        <script src="../Resources/Scripts/require.config.js" type="text/javascript" defer="defer">
        </script>
        <script src="../Resources/Scripts/foundation.6.2.3_custom.js" type="text/javascript" defer="defer">
        </script>
        <script src="../Resources/Scripts/plugins.min.js" type="text/javascript" defer="defer">
        </script>
        <script src="../Resources/Scripts/MadCapAll.js" type="text/javascript" defer="defer">
        </script>
        <script src="/assets/scripts/locale-cookie-setter.js">
        </script>
        <script src="/assets/scripts/insert-header-footer-v2.js">
        </script>
        <script src="/assets/scripts/top-content-dropdown.js">
        </script>
        <script src="https://assets.adobedtm.com/e0948d5bd3c9/cb9eebac40e3/launch-bf932e064195.min.js" async="true">
        </script>
        <script src="resources/scripts/claris.js">
        </script>
        <script src="resources/scripts/html-to-markdown.js">
        </script>
        <script src="resources/scripts/copy-as-markdown.js">
        </script>
        <script src="resources/scripts/legacy-list-fix.js">
        </script>
    </head>
    <body>
        <div class="foundation-wrap off-canvas-wrapper">
            <div class="off-canvas-wrapper-inner" data-off-canvas-wrapper="">
                <aside class="off-canvas position-right" role="complementary" id="offCanvas" data-off-canvas="" data-position="right" data-mc-ignore="true">
                    <ul class="off-canvas-accordion vertical menu off-canvas-list" data-accordion-menu="" data-mc-back-link="Back" data-mc-css-tree-node-expanded="is-accordion-submenu-parent" data-mc-css-tree-node-collapsed="is-accordion-submenu-parent" data-mc-css-sub-menu="vertical menu is-accordion-submenu nested" data-mc-include-indicator="False" data-mc-include-icon="False" data-mc-include-parent-link="True" data-mc-include-back="False" data-mc-defer-expand-event="True" data-mc-expanded-event="down.zf.accordionMenu up.zf.accordionMenu" data-mc-expand-event="click.zf.accordionMenu" data-mc-toc="True">
                    </ul>
                </aside>
                <div class="off-canvas-content inner-wrap" data-off-canvas-content="">
                    <div data-sticky-container="" class="title-bar-container">
                        <nav class="title-bar tab-bar sticky" aria-label="Main navigation and search" data-sticky="" data-options="marginTop:0" style="width:100%" data-sticky-on="only screen and (max-width: 1024px)" data-mc-ignore="true"><a class="skip-to-content fluid-skip showOnFocus" href="#">Skip To Main Content</a>
                            <div class="middle title-bar-section outer-row clearfix">
                                <div class="menu-icon-container relative clearfix">
                                    <div class="central-account-wrapper">
                                        <div class="central-dropdown"><a class="central-account-drop"><span class="central-account-image"></span><span class="central-account-text">Account</span></a>
                                            <div class="central-dropdown-content"><a class="MCCentralLink central-dropdown-content-settings">Settings</a>
                                                <hr class="central-separator" /><a class="MCCentralLink central-dropdown-content-logout">Logout</a>
                                            </div>
                                        </div>
                                    </div>
                                    <button class="menu-icon" aria-label="Show Navigation Panel" data-toggle="offCanvas"><span></span>
                                    </button>
                                </div>
                            </div>
                            <div class="title-bar-layout outer-row">
                                <div class="logo-wrapper"><a class="logo" href="index.html" alt="Claris logo"></a>
                                </div>
                                <div class="navigation-wrapper nocontent">
                                    <ul class="navigation clearfix" data-mc-css-tree-node-has-children="has-children" data-mc-css-sub-menu="sub-menu" data-mc-expand-event="mouseenter" data-mc-top-nav-menu="True" data-mc-max-depth="3" data-mc-include-icon="False" data-mc-include-indicator="False" data-mc-include-children="True" data-mc-include-siblings="True" data-mc-include-parent="True" data-mc-toc="True">
                                        <li class="placeholder" style="visibility:hidden"><a>placeholder</a>
                                        </li>
                                    </ul>
                                </div>
                                <div class="central-account-wrapper">
                                    <div class="central-dropdown"><a class="central-account-drop"><span class="central-account-image"></span><span class="central-account-text">Account</span></a>
                                        <div class="central-dropdown-content"><a class="MCCentralLink central-dropdown-content-settings">Settings</a>
                                            <hr class="central-separator" /><a class="MCCentralLink central-dropdown-content-logout">Logout</a>
                                        </div>
                                    </div>
                                </div>
                                <div class="nav-search-wrapper">
                                    <div class="nav-search row">
                                        <form class="search" action="#">
                                            <div class="search-bar search-bar-container needs-pie">
                                                <input class="search-field needs-pie" type="search" aria-label="Search Field" placeholder="Search" />
                                                <div class="search-filter-wrapper"><span class="invisible-label" id="search-filters-label">Filter: </span>
                                                    <div class="search-filter" aria-haspopup="true" aria-controls="sf-content" aria-expanded="false" aria-label="Search Filter" title="All Files" role="button" tabindex="0">
                                                    </div>
                                                    <div class="search-filter-content" id="sf-content">
                                                        <ul>
                                                            <li>
                                                                <button class="mc-dropdown-item" aria-labelledby="search-filters-label filterSelectorLabel-00001"><span id="filterSelectorLabel-00001">All Files</span>
                                                                </button>
                                                            </li>
                                                        </ul>
                                                    </div>
                                                </div>
                                                <div class="search-submit-wrapper" dir="ltr">
                                                    <div class="search-submit" title="Search" role="button" tabindex="0"><span class="invisible-label">Submit Search</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        </nav>
                    </div>
                    <div class="main-section">
                        <div class="row outer-row sidenav-layout">
                            <nav class="sidenav-wrapper">
                                <div class="sidenav-container">
                                    <ul class="off-canvas-accordion vertical menu sidenav" data-accordion-menu="" data-mc-css-tree-node-expanded="is-accordion-submenu-parent" data-mc-css-tree-node-collapsed="is-accordion-submenu-parent" data-mc-css-sub-menu="''vertical menu accordion-menu'' is-accordion-submenu nested" data-mc-include-indicator="False" data-mc-include-icon="False" data-mc-include-parent-link="False" data-mc-include-back="False" data-mc-defer-expand-event="True" data-mc-expanded-event="down.zf.accordionMenu up.zf.accordionMenu" data-mc-expand-event="click.zf.accordionMenu" data-mc-toc="True" data-mc-side-nav-menu="True">
                                        <li class="tree-node tree-node-preloaded"><a href="index.html">Home</a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="basics.html" aria-expanded="false">FileMaker Pro basics<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="adding-viewing-data.html" aria-expanded="false">Adding and viewing data<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="finding-records.html" aria-expanded="false">Finding records<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="sorting-records.html" aria-expanded="false">Sorting records<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="previewing-printing.html" aria-expanded="false">Previewing and printing information<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="creating-a-custom-app.html" aria-expanded="false">Creating a custom app<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="related-tables-files.html" aria-expanded="false">Working with related tables<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="layouts-and-reports.html" aria-expanded="false">Creating and managing layouts and reports<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="editing-objects-parts-background.html" aria-expanded="false">Editing objects, layout parts, and the layout background<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="creating-charts.html" aria-expanded="false">Creating charts from data<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="scripts.html" aria-expanded="false">Automating tasks with scripts<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="protecting-databases.html" aria-expanded="false">Managing security<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="sharing-files.html" aria-expanded="false">Sharing files on a network<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="saving-importing-exporting-data.html" aria-expanded="false">Saving, importing, and exporting data<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="publishing-databases-web.html" aria-expanded="false">Publishing databases on the web<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="odbc-jdbc.html" aria-expanded="false">Using ODBC and JDBC with FileMaker Pro<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="external-data-sources.html" aria-expanded="false">Accessing external data sources<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="using-advanced.html" aria-expanded="false">Using advanced tools<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                        </li>
                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="#" aria-expanded="true">Reference<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                            <ul class="''vertical menu accordion-menu''">
                                                <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="setting-preferences.html" aria-expanded="false">Changing settings<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="shortcuts-windows.html" aria-expanded="false">Keyboard shortcuts (Windows)<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="shortcuts-os-x.html" aria-expanded="false">Keyboard shortcuts (macOS)<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="functions-reference.html" aria-expanded="true">Functions reference<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                    <ul class="''vertical menu accordion-menu''">
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="text-functions.html" aria-expanded="false">Text functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="text-formatting-functions.html" aria-expanded="false">Text formatting functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="number-functions.html" aria-expanded="false">Number functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="date-functions.html" aria-expanded="false">Date functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="time-functions.html" aria-expanded="false">Time functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="timestamp-functions.html" aria-expanded="false">Timestamp functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="container-functions.html" aria-expanded="false">Container functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="japanese-functions.html" aria-expanded="false">Japanese functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="json-functions-category.html" aria-expanded="false">JSON functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="aggregate-functions.html" aria-expanded="false">Aggregate functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="repeating-functions.html" aria-expanded="false">Repeating functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="financial-functions.html" aria-expanded="false">Financial functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="trigonometric-functions.html" aria-expanded="false">Trigonometric functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="logical-functions.html" aria-expanded="false">Logical functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="artificial-intelligence-functions.html" aria-expanded="false">Artificial intelligence functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="miscellaneous-functions.html" aria-expanded="false">Miscellaneous functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="get-functions.html" aria-expanded="false">Get functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="design-functions.html" aria-expanded="false">Design functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                        </li>
                                                        <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="mobile-functions.html" aria-expanded="true">Mobile functions<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                            <ul class="''vertical menu accordion-menu''">
                                                                <li class="tree-node tree-node-preloaded tree-node-selected"><a href="#" class="selected">GetAVPlayerAttribute</a>
                                                                </li>
                                                                <li class="tree-node tree-node-preloaded"><a href="getsensor.html">GetSensor</a>
                                                                </li>
                                                                <li class="tree-node tree-node-preloaded"><a href="location.html">Location</a>
                                                                </li>
                                                                <li class="tree-node tree-node-preloaded"><a href="locationvalues.html">LocationValues</a>
                                                                </li>
                                                                <li class="tree-node tree-node-preloaded"><a href="rangebeacons.html">RangeBeacons</a>
                                                                </li>
                                                            </ul>
                                                        </li>
                                                    </ul>
                                                </li>
                                                <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="script-steps-reference.html" aria-expanded="false">Script steps reference<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="script-triggers-reference.html" aria-expanded="false">Script triggers reference<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded"><a href="error-codes.html">FileMaker error codes</a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded"><a href="curl-options.html">Supported cURL options</a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded"><a href="named-constants-keywords.html">Named constants and other special keywords</a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="converting-files.html" aria-expanded="false">Converting files from FileMaker Pro 11 and earlier<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded has-children is-accordion-submenu-parent"><a href="maintaining-recovering-databases.html" aria-expanded="false">Maintaining and recovering FileMaker Pro databases<span class="submenu-toggle-container" role="button" tabindex="0" aria-expanded="false"><span class="submenu-toggle"></span></span></a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded"><a href="feature-compatibility.html">FileMaker features not compatible with previous versions</a>
                                                </li>
                                                <li class="tree-node tree-node-preloaded"><a href="troubleshooting.html">Troubleshooting</a>
                                                </li>
                                            </ul>
                                        </li>
                                    </ul>
                                </div>
                            </nav>
                            <div class="body-container">
                                <div data-mc-content-body="True">
                                    <div id="copy-markdown-strings" style="display:none;" aria-hidden="true"><span data-string="success"><span class="mc-variable shared-localize.copy-markdown-success variable">Copied to clipboard.</span></span><span data-string="error"><span class="mc-variable shared-localize.copy-markdown-error variable">Failed to copy to clipboard.</span></span>
                                    </div>
                                    <div id="top-content-container">
                                        <div id="title-and-toolbar">
                                            <div class="buttons popup-container clearfix topicToolbarProxy _Skins_TopicToolbar mc-component nocontent" style="mc-topic-toolbar-items: RemoveHighlight CopyAsMarkdown PreviousTopic SelectTOC Print NextTopic;">
                                                <div class="button-group-container-left">
                                                    <button class="button needs-pie remove-highlight-button" title="Remove highlights">
                                                        <div>
                                                            <div role="img" class="button-icon-wrapper" aria-label="Remove Highlights">
                                                                <div class="button-icon"> </div>
                                                            </div>
                                                        </div>
                                                    </button>
                                                    <button class="button needs-pie copy-as-markdown-button" title="Copy page as Markdown">
                                                        <div>
                                                            <div role="img" class="button-icon-wrapper" aria-label="Copy page as Markdown">
                                                                <div class="button-icon"> </div>
                                                            </div>
                                                        </div>
                                                    </button>
                                                    <button class="button needs-pie previous-topic-button" title="Navigate previous" disabled="true">
                                                        <div>
                                                            <div role="img" class="button-icon-wrapper" aria-label="Navigate previous">
                                                                <div class="button-icon"> </div>
                                                            </div>
                                                        </div>
                                                    </button>
                                                    <button class="button needs-pie print-button" title="Print">
                                                        <div>
                                                            <div role="img" class="button-icon-wrapper" aria-label="Print">
                                                                <div class="button-icon"> </div>
                                                            </div>
                                                        </div>
                                                    </button>
                                                    <button class="button needs-pie next-topic-button" title="Navigate next" disabled="true">
                                                        <div>
                                                            <div role="img" class="button-icon-wrapper" aria-label="Navigate next">
                                                                <div class="button-icon"> </div>
                                                            </div>
                                                        </div>
                                                    </button>
                                                </div>
                                            </div>
                                            <p class="doc-title"><span class="mc-variable doc-specific-variables.doc-title variable">Claris FileMaker Pro Help</span>
                                            </p>
                                        </div>
                                        <div id="breadcrumbs-container">
                                            <div class="nocontent">
                                                <div class="MCBreadcrumbsBox_0 breadcrumbs" role="navigation" aria-label="Breadcrumbs" data-mc-breadcrumbs-divider="&gt;" data-mc-breadcrumbs-count="3" data-mc-toc="True"><span class="MCBreadcrumbsPrefix"> </span>
                                                </div>
                                            </div>
                                        </div>
                                        <div id="search-container">
                                            <form class="search" action="#">
                                                <div class="search-bar search-bar-container needs-pie">
                                                    <input class="search-field needs-pie" type="search" aria-label="Search Field" placeholder="Search" />
                                                    <div class="search-filter-wrapper"><span class="invisible-label" id="search-filters-label">Filter: </span>
                                                        <div class="search-filter" aria-haspopup="true" aria-controls="sf-content" aria-expanded="false" aria-label="Search Filter" title="All Files" role="button" tabindex="0">
                                                        </div>
                                                        <div class="search-filter-content" id="sf-content">
                                                            <ul>
                                                                <li>
                                                                    <button class="mc-dropdown-item" aria-labelledby="search-filters-label filterSelectorLabel-00001"><span id="filterSelectorLabel-00001">All Files</span>
                                                                    </button>
                                                                </li>
                                                            </ul>
                                                        </div>
                                                    </div>
                                                    <div class="search-submit-wrapper" dir="ltr">
                                                        <div class="search-submit" title="Search" role="button" tabindex="0"><span class="invisible-label">Submit Search</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </form>
                                        </div>
                                        <div class="dropdown-arrow">
                                            <img class="arrow" src="" alt="" width="18px" />
                                        </div>
                                    </div>
                                    <div role="main" id="mc-main-content">
                                        <h1 class="func">GetAVPlayerAttribute</h1>
                                        <p class="ref-purpose-func"><span class="mc-variable ui-strings-functions.kDBAVPlayerAttrOp variable">Returns the setting of the specified attribute for the audio, video, or image file in a container field.</span>
                                        </p>
                                        <h2 class="ref-format-head" data-mc-autonum="Format"><span class="autonumber"><span>Format</span></span>&#160;</h2><pre class="ref-format">GetAVPlayerAttribute ( attributeName )</pre>
                                        <h2 class="ref-param-head" data-mc-autonum="Parameters"><span class="autonumber"><span>Parameters</span></span>&#160;</h2>
                                        <p><code>attributeName</code> - the name of a supported attribute (see below).</p>
                                        <h2 class="ref-return-head" data-mc-autonum="Data type returned"><span class="autonumber"><span>Data type returned</span></span>&#160;</h2>
                                        <p>text, number</p>
                                        <h2 class="ref-orig-head" data-mc-autonum="Originated in version"><span class="autonumber"><span>Originated in version</span></span>&#160;</h2>
                                        <p class="or-origin">14.0</p>
                                        <h2 class="ref-desc-head" data-mc-autonum="Description"><span class="autonumber"><span>Description</span></span>&#160;</h2>
                                        <p>This function is used in FileMaker&#160;Go. If this function is called when the media file is playing or is paused, it returns a value for the file''s current playback state. If the function is called when no media is playing, it returns a value for the state of the media file most recently played. If the function is called when no media file has been played, it returns an empty string or<strong> 0</strong>.</p>
                                        <h2>Attributes</h2>
                                        <table cellspacing="0" class="TableStyle-StandardTable" style="mc-table-style: url(''resources/tablestyles/standardtable.css'');">
                                            <thead>
                                                <tr class="TableStyle-StandardTable-Head-Header1">
                                                    <td class="TableStyle-StandardTable-HeadE-Column1-Header1">
                                                        <p>Attribute</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-HeadE-Column1-Header1">
                                                        <p>Returns</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-HeadD-Column1-Header1">
                                                        <p>Data type returned</p>
                                                    </td>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>all</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>All the attributes and their values.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>text</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>sourceType</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>The source type used for audio and video files: <br /><strong>0 </strong>(None) <br /><strong>1 </strong>(URL) <br /><strong>2 (</strong>Field) <br /><strong>3 </strong>(Layout object)<br /><strong>4 </strong>(Active object) </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>source</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>The URL, field name, or layout object name. If <code>sourceType</code> is 4 (active object), then <code>source</code> returns an empty string.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>text</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>playbackState</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>A number representing the state of the media playback: <br /><strong>0 </strong>(Stopped) <br /><strong>1 </strong>(Playing) <br /><strong>2 </strong>(Paused) </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>presentation</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>The method used to display the media:<br /><strong>0 </strong>(Embedded) <br /><strong>1 </strong>(Full Screen) <br /><strong>2 </strong>(Full Screen Only) <br /><strong>3 </strong>(Audio Only)<br /><strong>4 </strong>(Embedded Only)</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>position</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>The position (in seconds) currently playing in the media.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>startOffset</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>The starting position of the playback (in seconds).</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>endOffset</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>The end position of the playback (in seconds); returns <strong>0</strong> if playing to the end of the media.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>duration</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>The length of time (in seconds) that the audio or video file will play.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>triggerEvent</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>Indicates why the last OnObjectAVPlayerChange or OnFileAVPlayerChange script triggers were activated: <br /><strong>0 </strong>(Internal) <br /><strong>1 </strong>(Script) <br /><strong>2 </strong>(Remote) </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>triggerEventDetail</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>Provides information about the event that activated the last OnObjectAVPlayerChange or OnFileAVPlayerChange script trigger: <br /><strong>0 </strong>(Unknown)<br /><strong>1</strong> (RemotePlayMedia) <br /><strong>2</strong> (RemotePause) <br /><strong>3</strong> (RemoteTogglePlayPause) <br /><strong>4</strong> (RemotePlayNext)<br /><strong>5</strong> (RemotePlayPrevious) <br /><strong>6</strong> (RemoteSeek)<br /><strong>7</strong> (RemoteStop) <br /><strong>8</strong> (ScriptPlayMedia)<br /><strong>9</strong> (ScriptChangePresentation) <br /><strong>10</strong> (ScriptTogglePlayPause)<br /><strong>11</strong> (ScriptStop) <br /><strong>12</strong> (ScriptChangeSetting)<br /><strong>13</strong> (InternalTogglePlayPause) <br /><strong>14</strong> (InternalChangePresentation)<br /><strong>15</strong> (InternalSeek) <br /><strong>16</strong> (InternalStop)<br /><strong>17</strong> (InternalChangeZoom)<br /><strong>18</strong> (InternalChangeVolume) <br /><strong>19</strong> (InternalChangePIP)<br /><strong>20</strong> (InternalChangeExternalPlayback) </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>sequence</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>Indicates which media file should be played next:<br /><strong>0 </strong>(None) <br /><strong>-1 </strong>(Go to previous) <br /><strong>+1 </strong>(Go to next) </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>result</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><strong>0</strong> if playback ends successfully; returns <strong>1</strong> if playback ends due to an error.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>hideControls</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><strong>1 </strong>(Yes)<strong> </strong>if the playback controls are hidden; otherwise returns <strong>0 </strong>(No).</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>disableInteraction</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><strong>1 </strong>(Yes)<strong> </strong>if users cannot interact with the playback; otherwise returns <strong>0 </strong>(No).</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>disableExternalControls</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><strong>1 </strong>(Yes)<strong> </strong>if the iOS or iPadOS playback controls on the lock screen or on the control panel are disabled when the media is playing or is paused; otherwise, returns <strong>0 </strong>(No).</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>pauseInBackground</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><strong>0 </strong>Video is paused (except for Picture in Picture) and audio continues to play when FileMaker&#160;Go moves to the background.<br /><strong>1 </strong>Both audio and video are paused when FileMaker&#160;Go moves to the background.<br /><strong>2 </strong>Both audio and video continue to play when FileMaker&#160;Go moves to the background.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>zoom</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>Indicates how the video is displayed:<br /><strong>0 </strong>(Fit) The aspect ratio is preserved, and the video is scaled to fit within the playback area.<br /><strong>1 </strong>(Fill) The aspect ratio is preserved, and the video is scaled to fill the playback area.<br /><strong>2 </strong>(Stretch) The video is stretched to fill the playback area, but the aspect ratio is not preserved.<br /><strong>3 </strong>(Fit Only) Users are not allowed to change the zoom setting to Fill or Stretch.<br /><strong>4 </strong>(Fill Only) Users are not allowed to change the zoom setting to Fit or Stretch.<br /><strong>5 </strong>(Stretch Only) Users are not allowed to change the zoom setting to Fit or Fill.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>volume</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>Indicates the volume level for the audio.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>pictureInPicture</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>Specifies whether the video is displayed as Picture in Picture:<br /><strong>0 </strong>(Not Available) <br /><strong>1 </strong>(Not Active)<br /><strong>2 </strong>(Active)</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>externalPlayback</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>Specifies whether a video is played on an external device, such as Apple&#160;TV via AirPlay:<br /><strong>0 </strong>(Not Available) <br /><strong>1 </strong>(Not Active)<br /><strong>2 </strong>(Active)</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>imageSourceType</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>The source type used for images: <br /><strong>0 </strong>(None) <br /><strong>1 </strong>(URL) <br /><strong>2 </strong>(Field) <br /><strong>3 </strong>(Layout object)<br /><strong>4 </strong>(Active object)</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p><code>imageSource</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyE-Column1-Body1">
                                                        <p>The URL, field name, or layout object name for images. </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyD-Column1-Body1">
                                                        <p>text</p>
                                                    </td>
                                                </tr>
                                                <tr class="TableStyle-StandardTable-Body-Body1">
                                                    <td class="TableStyle-StandardTable-BodyB-Column1-Body1">
                                                        <p><code>imageDuration</code>
                                                        </p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyB-Column1-Body1">
                                                        <p>The length of time (in seconds) that the images should be displayed.</p>
                                                    </td>
                                                    <td class="TableStyle-StandardTable-BodyA-Column1-Body1">
                                                        <p>number</p>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                        <h2 class="ref-example1-head" data-mc-autonum="Example 1"><span class="autonumber"><span>Example 1</span></span>&#160;</h2>
                                        <p>Stops playing a media file if it is currently playing.</p>
                                        <div class="codeSnippet"><a class="codeSnippetCopyButton" role="button" href="javascript:void(0);">Copy</a>
                                            <div class="codeSnippetBody" data-mc-use-line-numbers="False" data-mc-line-number-start="1" data-mc-continue="False"><pre><code>If [GetAVPlayerAttribute("playbackState") = 1]<br />&#160;&#160;&#160;&#160;AVPlayer Set Playback State [Stopped]<br />End If</code></pre>
                                            </div>
                                        </div>
                                        <h2 class="ref-examplen-head" data-mc-autonum="Example 2"><span class="autonumber"><span>Example 2</span></span>&#160;</h2>
                                        <p>Checks the duration of a media file and displays a message if it is longer than 30 minutes.</p>
                                        <div class="codeSnippet"><a class="codeSnippetCopyButton" role="button" href="javascript:void(0);">Copy</a>
                                            <div class="codeSnippetBody" data-mc-use-line-numbers="False" data-mc-line-number-start="1" data-mc-continue="False"><pre><code>If [GetAVPlayerAttribute("duration") &gt; 1800]<br />&#160;&#160;&#160;&#160;Show Custom Dialog ["Exceeds Maximum Duration"; "The current video is longer than 30 minutes."]<br />Else<br />&#160;&#160;&#160;&#160;AVPlayer Play [Field: Library::Video]<br />End If</code></pre>
                                            </div>
                                        </div>
                                        <h2 class="related-head" data-mc-autonum="Related topics"><span class="autonumber"><span>Related topics</span></span>&#160;</h2>
                                        <ul class="related-list">
                                            <li><a href="functions-reference.html" class="MCXref xref">Functions reference</a>
                                            </li>
                                            <li><a href="formulas.html" class="MCXref xref">About formulas</a>
                                            </li>
                                            <li><a href="functions.html" class="MCXref xref">About functions</a>
                                            </li>
                                            <li><a href="calculation-fields.html" class="MCXref xref">Defining calculation fields</a>
                                            </li>
                                            <li><a href="operators-in-formulas.html" class="MCXref xref">Using operators in formulas</a>
                                            </li>
                                            <li><a class="LinktoScriptStepU MCXref xref xrefLinktoScriptStepU" href="avplayer-play.html">AVPlayer Play script step</a>
                                            </li>
                                            <li><a class="LinktoScriptStepU MCXref xref xrefLinktoScriptStepU" href="avplayer-set-options.html">AVPlayer Set Options script step</a>
                                            </li>
                                            <li><a class="LinktoScriptStepU MCXref xref xrefLinktoScriptStepU" href="avplayer-set-playback-state.html">AVPlayer Set Playback State script step</a>
                                            </li>
                                        </ul>
                                    </div>
                                    <p class="feedback">Was this topic helpful? <a href="https://www.claris.com/redirects/fmm26_admin.html?page=feedback&amp;lang=en" target="_blank">Send feedback</a>.</p>
                                    <div class="footer-alt">
                                        <div class="home-master-page-footer-alt">
                                            <div>
                                                <p>Copyright © <span class="mc-variable shared.copyright-year variable">2026</span>, Claris&#160;International&#160;Inc.</p>
                                            </div>
                                            <div>
                                                <p><a id="footer-legal-info" href="https://www.claris.com/company/legal/claris-documentation.html">Legal information</a>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div><a data-close="true"></a>
                </div>
            </div>
        </div>
    </body>
</html>', '2832e2f996156c97c3229cc98e81b80aa215c7ca4fa396675292ee52da95aa44');
