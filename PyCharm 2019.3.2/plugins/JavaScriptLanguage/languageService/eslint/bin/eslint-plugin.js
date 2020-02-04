"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
exports.__esModule = true;
var ESLintResponse = /** @class */ (function () {
    function ESLintResponse() {
    }
    return ESLintResponse;
}());
var FileKind;
(function (FileKind) {
    FileKind["js"] = "js";
    FileKind["ts"] = "ts";
    FileKind["html"] = "html";
    FileKind["vue"] = "vue";
})(FileKind || (FileKind = {}));
var ESLintPlugin = /** @class */ (function () {
    function ESLintPlugin(state) {
        this.includeSourceText = state.includeSourceText;
        this.additionalRulesDirectory = state.additionalRootDirectory;
        var eslintPackagePath;
        if (state.standardPackagePath != null) {
            var standardPackagePath = normalizePath(state.standardPackagePath);
            this.standardLinter = require(standardPackagePath);
            // Standard doesn't provide API to check if file is ignored (https://github.com/standard/standard/issues/1448).
            // The only way is to use ESLint for that.
            eslintPackagePath = findESLintPackagePath(standardPackagePath);
        }
        else {
            eslintPackagePath = state.eslintPackagePath;
        }
        eslintPackagePath = normalizePath(eslintPackagePath);
        this.options = require(eslintPackagePath + "lib/options");
        this.cliEngineCtor = require(eslintPackagePath + "lib/api").CLIEngine;
    }
    ESLintPlugin.prototype.onMessage = function (p, writer) {
        var request = JSON.parse(p);
        var response = new ESLintResponse();
        response.request_seq = request.seq;
        response.command = request.command;
        try {
            if (request.command === ESLintPlugin.GetErrors) {
                response.body = this.filterSourceIfNeeded(this.getErrors(request.arguments));
            }
            else if (request.command === ESLintPlugin.FixErrors) {
                response.body = this.filterSourceIfNeeded(this.fixErrors(request.arguments));
            }
            else {
                response.error = "Unknown command: " + request.command;
            }
        }
        catch (e) {
            response.isNoConfigFile = "no-config-found" === e.messageTemplate
                || (e.message && containsString(e.message.toString(), "No ESLint configuration found"));
            response.error = e.toString() + "\n\n" + e.stack;
        }
        writer.write(JSON.stringify(response));
    };
    ESLintPlugin.prototype.filterSourceIfNeeded = function (body) {
        if (!this.includeSourceText) {
            body.results.forEach(function (value) {
                delete value.source;
                value.messages.forEach(function (msg) { return delete msg.source; });
            });
        }
        return body;
    };
    ESLintPlugin.prototype.getErrors = function (getErrorsArguments) {
        return this.invokeESLint(getErrorsArguments);
    };
    ESLintPlugin.prototype.fixErrors = function (fixErrorsArguments) {
        return this.invokeESLint(fixErrorsArguments, { fix: true });
    };
    ESLintPlugin.prototype.invokeESLint = function (requestArguments, additionalOptions) {
        if (additionalOptions === void 0) { additionalOptions = {}; }
        var parsedCommandLineOptions = translateOptions(this.options.parse(requestArguments.extraOptions || ""));
        var options = __assign({}, parsedCommandLineOptions, additionalOptions);
        options.ignorePath = requestArguments.ignoreFilePath;
        if (requestArguments.configPath != null) {
            options.configFile = requestArguments.configPath;
        }
        if (this.additionalRulesDirectory != null && this.additionalRulesDirectory.length > 0) {
            if (options.rulePaths == null) {
                options.rulePaths = [this.additionalRulesDirectory];
            }
            else {
                options.rulePaths.push(this.additionalRulesDirectory);
            }
        }
        var cliEngine = new this.cliEngineCtor(options);
        if (cliEngine.isPathIgnored(requestArguments.fileName)) {
            return createEmptyResult();
        }
        if (this.standardLinter != null) {
            var standardOptions = { filename: requestArguments.fileName };
            if (additionalOptions.fix) {
                standardOptions.fix = true;
            }
            return this.standardLinter.lintTextSync(requestArguments.content, standardOptions);
        }
        var config = cliEngine.getConfigForFile(requestArguments.fileName);
        if (!isFileKindAcceptedByConfig(config, requestArguments.fileKind)) {
            return createEmptyResult();
        }
        return cliEngine.executeOnText(requestArguments.content, requestArguments.fileName);
    };
    ESLintPlugin.GetErrors = "GetErrors";
    ESLintPlugin.FixErrors = "FixErrors";
    return ESLintPlugin;
}());
exports.ESLintPlugin = ESLintPlugin;
function isFileKindAcceptedByConfig(config, fileKind) {
    var plugins = config.plugins;
    function hasPlugin(toCheck) {
        return plugins != null && plugins
            .filter(function (value) { return value == toCheck || value == "eslint-plugin-" + toCheck; }).length > 0;
    }
    function hasParser(parser) {
        return (config.parser != null && containsString(normalizePath(config.parser), parser))
            || (config.parserOptions != null && parser == config.parserOptions["parser"]);
    }
    if (fileKind === FileKind.ts) {
        return hasPlugin("typescript") || hasParser("babel-eslint") || hasParser("typescript-eslint-parser")
            || hasParser("@typescript-eslint/parser");
    }
    if (fileKind === FileKind.html) {
        return hasPlugin("html");
    }
    if (fileKind === FileKind.vue) {
        return (
        //eslint-plugin-html used to process .vue files prior to v5
        hasPlugin("html") ||
            //eslint-plugin-vue in plugins used to be enough to process .vue files prior to v3
            hasPlugin("vue") ||
            hasParser("vue-eslint-parser"));
    }
    return true;
}
function containsString(src, toFind) {
    return src != null && src.indexOf(toFind) >= 0;
}
function normalizePath(eslintPackagePath) {
    if (eslintPackagePath.charAt(eslintPackagePath.length - 1) !== '/' &&
        eslintPackagePath.charAt(eslintPackagePath.length - 1) !== '\\') {
        eslintPackagePath = eslintPackagePath + '/';
    }
    return eslintPackagePath.split("\\").join("/");
}
function findESLintPackagePath(standardPackagePath) {
    var requirePath = require.resolve("eslint", { paths: [standardPackagePath] });
    requirePath = requirePath.split("\\").join("/");
    var eslintPackageStr = "/eslint/";
    var ind = requirePath.lastIndexOf(eslintPackageStr);
    if (ind < 0) {
        throw Error("Cannot find eslint package for " + requirePath);
    }
    return requirePath.substring(0, ind + eslintPackageStr.length);
}
function createEmptyResult() {
    return { results: [], warningCount: 0, fixableWarningCount: 0, fixableErrorCount: 0, errorCount: 0 };
}
// taken from private part of eslint(lib/cli.js), we need it here
/**
 * Translates the CLI options into the options expected by the CLIEngine.
 * @param {Object} cliOptions The CLI options to translate.
 * @returns {CLIEngine.Options} The options object for the CLIEngine.
 * @private
 */
function translateOptions(cliOptions) {
    return {
        envs: cliOptions.env,
        extensions: cliOptions.ext,
        rules: cliOptions.rule,
        plugins: cliOptions.plugin,
        globals: cliOptions.global,
        ignore: cliOptions.ignore,
        ignorePath: cliOptions.ignorePath,
        ignorePattern: cliOptions.ignorePattern,
        configFile: cliOptions.config,
        rulePaths: cliOptions.rulesdir,
        useEslintrc: cliOptions.eslintrc,
        parser: cliOptions.parser,
        parserOptions: cliOptions.parserOptions,
        cache: cliOptions.cache,
        cacheFile: cliOptions.cacheFile,
        cacheLocation: cliOptions.cacheLocation,
        allowInlineConfig: cliOptions.inlineConfig,
        reportUnusedDisableDirectives: cliOptions.reportUnusedDisableDirectives
    };
}
//# sourceMappingURL=eslint-plugin.js.map