using System;
using System.Buffers.Binary;
using System.IO;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;


namespace KardanSoft.Tools.KstpClient;


public sealed class KstpNetworkClient :
    IAsyncDisposable
{
    private readonly string _host;
    private readonly int _port;

    private readonly SemaphoreSlim _requestLock =
        new(1, 1);

    private TcpClient? _tcpClient;
    private NetworkStream? _stream;


    public KstpNetworkClient(
        string host,
        int port
    )
    {
        if (
            string.IsNullOrWhiteSpace(host)
        )
        {
            throw new ArgumentException(
                "Host is required.",
                nameof(host)
            );
        }


        if (
            port < 1
            || port > 65535
        )
        {
            throw new ArgumentOutOfRangeException(
                nameof(port)
            );
        }


        _host = host.Trim();
        _port = port;
    }


    public bool IsConnected =>
        _tcpClient?.Connected == true
        && _stream is not null;


    // ========================================================
    // CONNECT
    // ========================================================

    public async Task ConnectAsync(
        CancellationToken cancellationToken =
            default
    )
    {
        if (IsConnected)
        {
            return;
        }


        await DisconnectAsync();


        TcpClient client =
            new()
            {
                NoDelay = true,
            };


        try
        {
            await client.ConnectAsync(
                _host,
                _port,
                cancellationToken
            );


            _tcpClient = client;
            _stream = client.GetStream();
        }
        catch
        {
            client.Dispose();
            throw;
        }
    }


    // ========================================================
    // SEND ONE REQUEST
    // ========================================================

    public async Task<KstpFrame> SendRequestAsync(
        MessageType messageType,
        uint requestId,
        object payload,
        CancellationToken cancellationToken =
            default
    )
    {
        await _requestLock.WaitAsync(
            cancellationToken
        );


        try
        {
            if (
                _stream is null
                || !IsConnected
            )
            {
                throw new InvalidOperationException(
                    "KSTP client is not connected."
                );
            }


            byte[] request =
                KstpProtocol.EncodeFrame(
                    messageType,
                    requestId,
                    payload
                );


            await _stream.WriteAsync(
                request,
                cancellationToken
            );


            await _stream.FlushAsync(
                cancellationToken
            );


            KstpFrame response =
                await ReadFrameAsync(
                    _stream,
                    cancellationToken
                );


            if (
                response.RequestId
                != requestId
            )
            {
                throw new InvalidDataException(
                    "KSTP response request ID mismatch. "
                    + $"Expected={requestId}, "
                    + $"Received={response.RequestId}."
                );
            }


            if (
                response.MessageType
                    != MessageType.ResponseOk
                &&
                response.MessageType
                    != MessageType.ResponseError
            )
            {
                throw new InvalidDataException(
                    "Expected RESPONSE_OK or "
                    + "RESPONSE_ERROR, received "
                    + $"{response.MessageType}."
                );
            }


            return response;
        }
        finally
        {
            _requestLock.Release();
        }
    }


    // ========================================================
    // READ COMPLETE FRAME
    // ========================================================

    private static async Task<KstpFrame>
        ReadFrameAsync(
            NetworkStream stream,
            CancellationToken cancellationToken
        )
    {
        byte[] header =
            new byte[
                KstpProtocol.HeaderSize
            ];


        await ReadExactAsync(
            stream,
            header,
            cancellationToken
        );


        uint payloadLength =
            BinaryPrimitives
                .ReadUInt32BigEndian(
                    header.AsSpan(
                        4,
                        4
                    )
                );


        if (
            payloadLength
            > KstpProtocol.MaxPayload
        )
        {
            throw new InvalidDataException(
                "Received KSTP payload exceeds "
                + $"{KstpProtocol.MaxPayload} bytes."
            );
        }


        byte[] payload =
            new byte[
                checked(
                    (int)payloadLength
                )
            ];


        if (
            payload.Length > 0
        )
        {
            await ReadExactAsync(
                stream,
                payload,
                cancellationToken
            );
        }


        byte[] completeFrame =
            new byte[
                header.Length
                + payload.Length
            ];


        Buffer.BlockCopy(
            header,
            0,
            completeFrame,
            0,
            header.Length
        );


        Buffer.BlockCopy(
            payload,
            0,
            completeFrame,
            header.Length,
            payload.Length
        );


        return KstpProtocol.DecodeFrame(
            completeFrame
        );
    }


    // ========================================================
    // TCP READ EXACTLY N BYTES
    // ========================================================

    private static async Task ReadExactAsync(
        NetworkStream stream,
        Memory<byte> buffer,
        CancellationToken cancellationToken
    )
    {
        int offset = 0;


        while (
            offset < buffer.Length
        )
        {
            int received =
                await stream.ReadAsync(
                    buffer[offset..],
                    cancellationToken
                );


            if (
                received == 0
            )
            {
                throw new EndOfStreamException(
                    "TCP connection closed while "
                    + "receiving a KSTP frame."
                );
            }


            offset += received;
        }
    }


    // ========================================================
    // DISCONNECT
    // ========================================================

    public Task DisconnectAsync()
    {
        try
        {
            _stream?.Close();
        }
        catch
        {
            // Ignore socket shutdown errors.
        }


        try
        {
            _tcpClient?.Close();
        }
        catch
        {
            // Ignore socket shutdown errors.
        }


        _stream = null;
        _tcpClient = null;


        return Task.CompletedTask;
    }


    public async ValueTask DisposeAsync()
    {
        await DisconnectAsync();

        _requestLock.Dispose();
    }
}
