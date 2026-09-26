using System;
using System.Buffers.Binary;
using System.IO;
using System.Text.Encodings.Web;
using System.Text.Json;


namespace KardanSoft.Tools.KstpClient;


public enum MessageType : byte
{
    AllocateLocker = 0x01,
    OpenLocker = 0x02,
    ReleaseLocker = 0x03,

    ResponseOk = 0x80,
    ResponseError = 0x81,
}


public sealed record KstpFrame(
    MessageType MessageType,
    uint RequestId,
    JsonElement Payload
);


public static class KstpProtocol
{
    public const byte Version = 1;

    public const int HeaderSize = 12;

    public const int MaxPayload = 2048;


    private static readonly byte[] Magic =
    {
        0x4B,
        0x53,
    };


    private static readonly JsonSerializerOptions JsonOptions =
        new()
        {
            WriteIndented = false,

            // Python uses:
            //
            // ensure_ascii=False
            //
            // This keeps non-ASCII text as real UTF-8 instead
            // of unnecessarily escaping it as \uXXXX.
            Encoder =
                JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        };


    // ========================================================
    // ENCODE
    // ========================================================

    public static byte[] EncodeFrame(
        MessageType messageType,
        uint requestId,
        object payload
    )
    {
        ArgumentNullException.ThrowIfNull(
            payload
        );


        byte[] payloadBytes =
            JsonSerializer.SerializeToUtf8Bytes(
                payload,
                JsonOptions
            );


        ValidatePayloadObject(
            payloadBytes
        );


        if (
            payloadBytes.Length
            > MaxPayload
        )
        {
            throw new InvalidDataException(
                $"KSTP payload exceeds " +
                $"{MaxPayload} bytes."
            );
        }


        byte[] frame =
            new byte[
                HeaderSize
                + payloadBytes.Length
            ];


        // ----------------------------------------------------
        // MAGIC
        // ----------------------------------------------------

        frame[0] = Magic[0];
        frame[1] = Magic[1];


        // ----------------------------------------------------
        // VERSION
        // ----------------------------------------------------

        frame[2] = Version;


        // ----------------------------------------------------
        // MESSAGE TYPE
        // ----------------------------------------------------

        frame[3] =
            (byte)messageType;


        // ----------------------------------------------------
        // PAYLOAD LENGTH
        // UInt32 Big Endian
        // ----------------------------------------------------

        BinaryPrimitives.WriteUInt32BigEndian(
            frame.AsSpan(
                4,
                4
            ),
            (uint)payloadBytes.Length
        );


        // ----------------------------------------------------
        // REQUEST ID
        // UInt32 Big Endian
        // ----------------------------------------------------

        BinaryPrimitives.WriteUInt32BigEndian(
            frame.AsSpan(
                8,
                4
            ),
            requestId
        );


        // ----------------------------------------------------
        // JSON PAYLOAD
        // ----------------------------------------------------

        payloadBytes.CopyTo(
            frame.AsSpan(
                HeaderSize
            )
        );


        return frame;
    }


    // ========================================================
    // DECODE EXACT FRAME
    // ========================================================

    public static KstpFrame DecodeFrame(
        ReadOnlySpan<byte> data
    )
    {
        if (
            data.Length
            < HeaderSize
        )
        {
            throw new InvalidDataException(
                "Incomplete KSTP header."
            );
        }


        // ----------------------------------------------------
        // MAGIC
        // ----------------------------------------------------

        if (
            data[0] != Magic[0]
            ||
            data[1] != Magic[1]
        )
        {
            throw new InvalidDataException(
                "Invalid KSTP magic."
            );
        }


        // ----------------------------------------------------
        // VERSION
        // ----------------------------------------------------

        if (
            data[2] != Version
        )
        {
            throw new InvalidDataException(
                $"Unsupported KSTP version: " +
                $"{data[2]}."
            );
        }


        // ----------------------------------------------------
        // MESSAGE TYPE
        // ----------------------------------------------------

        MessageType messageType =
            (MessageType)data[3];


        if (
            !Enum.IsDefined(
                typeof(MessageType),
                messageType
            )
        )
        {
            throw new InvalidDataException(
                $"Unknown KSTP message type: " +
                $"0x{data[3]:X2}."
            );
        }


        // ----------------------------------------------------
        // PAYLOAD LENGTH
        // ----------------------------------------------------

        uint payloadLength =
            BinaryPrimitives.ReadUInt32BigEndian(
                data.Slice(
                    4,
                    4
                )
            );


        if (
            payloadLength
            > MaxPayload
        )
        {
            throw new InvalidDataException(
                $"KSTP payload exceeds " +
                $"{MaxPayload} bytes."
            );
        }


        int expectedLength =
            checked(
                HeaderSize
                + (int)payloadLength
            );


        if (
            data.Length
            < expectedLength
        )
        {
            throw new InvalidDataException(
                "Incomplete KSTP frame."
            );
        }


        if (
            data.Length
            > expectedLength
        )
        {
            throw new InvalidDataException(
                "Extra data after KSTP frame."
            );
        }


        // ----------------------------------------------------
        // REQUEST ID
        // ----------------------------------------------------

        uint requestId =
            BinaryPrimitives.ReadUInt32BigEndian(
                data.Slice(
                    8,
                    4
                )
            );


        // ----------------------------------------------------
        // JSON
        // ----------------------------------------------------

        byte[] payloadBytes =
            data.Slice(
                HeaderSize,
                (int)payloadLength
            ).ToArray();


        using JsonDocument document =
            JsonDocument.Parse(
                payloadBytes
            );


        if (
            document.RootElement.ValueKind
            != JsonValueKind.Object
        )
        {
            throw new InvalidDataException(
                "KSTP JSON payload must " +
                "be an object."
            );
        }


        return new KstpFrame(
            messageType,
            requestId,
            document.RootElement.Clone()
        );
    }


    // ========================================================
    // PAYLOAD VALIDATION
    // ========================================================

    private static void ValidatePayloadObject(
        byte[] payloadBytes
    )
    {
        using JsonDocument document =
            JsonDocument.Parse(
                payloadBytes
            );


        if (
            document.RootElement.ValueKind
            != JsonValueKind.Object
        )
        {
            throw new ArgumentException(
                "KSTP payload must serialize " +
                "to a JSON object."
            );
        }
    }
}
