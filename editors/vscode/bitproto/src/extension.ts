import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: vscode.ExtensionContext) {
    const serverPath = vscode.workspace.getConfiguration('bitprotoLanguageServer').get<string>('serverPath') || 'bitproto-language-server';

    let serverOptions: ServerOptions = {
        command: serverPath,
        transport: TransportKind.stdio,
    };

    let clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'bitproto' }],
        synchronize: {
            configurationSection: 'bitprotoLanguageServer',
            fileEvents: vscode.workspace.createFileSystemWatcher('**/.clientrc')
        },
    };

    client = new LanguageClient(
        'bitprotoLanguageServer',
        'Bitproto Language Server',
        serverOptions,
        clientOptions
    );

    client.start();
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
