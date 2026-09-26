using System;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Media;


namespace KardanSoft.Tools.KstpClient;


public partial class MainWindow : Window
{
    private KstpNetworkClient? _client;

    private bool _protocolReady;

    private int _nextRequestId =
        7000;


    public MainWindow()
    {
        InitializeComponent();

        Loaded += MainWindow_Loaded;
        Closed += MainWindow_Closed;
    }


    // ========================================================
    // STARTUP
    // ========================================================

    private void MainWindow_Loaded(
        object sender,
        RoutedEventArgs e
    )
    {
        RunProtocolSelfTest();
    }


    // ========================================================
    // PROTOCOL SELF TEST
    // ========================================================

    private void RunProtocolSelfTest()
    {
        AppendLog(
            "KSTP protocol self-test started."
        );


        try
        {
            byte[] actual =
                KstpProtocol.EncodeFrame(
                    MessageType.AllocateLocker,
                    1001,
                    new
                    {
                        locker_id = 17,
                        person_id = "P10025",
                    }
                );


            byte[] expected =
                Convert.FromHexString(
                    (
                        "4b 53 "
                        + "01 "
                        + "01 "
                        + "00 00 00 25 "
                        + "00 00 03 e9 "
                        + "7b 22 6c 6f 63 6b 65 72 5f "
                        + "69 64 22 3a 31 37 2c 22 70 "
                        + "65 72 73 6f 6e 5f 69 64 22 "
                        + "3a 22 50 31 30 30 32 35 22 7d"
                    )
                    .Replace(
                        " ",
                        ""
                    )
                );


            bool vectorOk =
                actual.SequenceEqual(
                    expected
                );


            KstpFrame decoded =
                KstpProtocol.DecodeFrame(
                    actual
                );


            bool decodeOk =
                decoded.MessageType
                    == MessageType.AllocateLocker

                &&

                decoded.RequestId
                    == 1001

                &&

                decoded.Payload
                    .GetProperty(
                        "locker_id"
                    )
                    .GetInt32()
                    == 17

                &&

                decoded.Payload
                    .GetProperty(
                        "person_id"
                    )
                    .GetString()
                    == "P10025";


            if (
                !vectorOk
                || !decodeOk
            )
            {
                throw new InvalidOperationException(
                    "KSTP compatibility test failed."
                );
            }


            _protocolReady = true;


            ProtocolStatusText.Text =
                "Self-test: PASS";

            ProtocolStatusText.Foreground =
                Brushes.Green;


            ConnectButton.IsEnabled =
                true;


            AppendLog(
                "KSTP reference vector | PASS"
            );

            AppendLog(
                "KSTP decoder          | PASS"
            );

            AppendLog(
                $"Frame length          | {actual.Length} bytes"
            );

            AppendLog(
                "JSON                  | "
                + Encoding.UTF8.GetString(
                    actual,
                    KstpProtocol.HeaderSize,
                    actual.Length
                    - KstpProtocol.HeaderSize
                )
            );

            AppendLog(
                "GUI ready."
            );
        }
        catch (Exception exc)
        {
            _protocolReady = false;


            ProtocolStatusText.Text =
                "Self-test: FAIL";

            ProtocolStatusText.Foreground =
                Brushes.Red;


            ConnectButton.IsEnabled =
                false;


            SetCommandButtons(
                false
            );


            AppendLog(
                "KSTP SELF-TEST | FAIL"
            );

            AppendLog(
                exc.GetType().Name
                + ": "
                + exc.Message
            );
        }
    }


    // ========================================================
    // CONNECT / DISCONNECT
    // ========================================================

    private async void ConnectButton_Click(
        object sender,
        RoutedEventArgs e
    )
    {
        if (
            _client is not null
        )
        {
            await DisconnectClientAsync(
                "Disconnected by user."
            );

            return;
        }


        string host =
            HostTextBox.Text.Trim();


        if (
            string.IsNullOrWhiteSpace(host)
        )
        {
            AppendLog(
                "ERROR | NanoPi IP is required."
            );

            return;
        }


        if (
            !int.TryParse(
                PortTextBox.Text.Trim(),
                out int port
            )
            ||
            port < 1
            ||
            port > 65535
        )
        {
            AppendLog(
                "ERROR | Invalid TCP port."
            );

            return;
        }


        ConnectButton.IsEnabled =
            false;

        HostTextBox.IsEnabled =
            false;

        PortTextBox.IsEnabled =
            false;


        ConnectionStatusText.Text =
            "Connecting...";

        ConnectionIndicator.Fill =
            Brushes.Goldenrod;


        AppendLog(
            $"CONNECT | {host}:{port}"
        );


        KstpNetworkClient client =
            new(
                host,
                port
            );


        try
        {
            using CancellationTokenSource timeout =
                new(
                    TimeSpan.FromSeconds(
                        5
                    )
                );


            await client.ConnectAsync(
                timeout.Token
            );


            _client = client;


            SetConnectedUi();


            AppendLog(
                "CONNECTED | PASS"
            );
        }
        catch (Exception exc)
        {
            await client.DisposeAsync();


            _client = null;


            SetDisconnectedUi();


            ConnectionStatusText.Text =
                "Connection failed";

            ConnectionIndicator.Fill =
                Brushes.Red;


            AppendLog(
                "CONNECT | FAIL"
            );

            AppendLog(
                exc.GetType().Name
                + ": "
                + exc.Message
            );
        }
    }


    private void SetConnectedUi()
    {
        ConnectionStatusText.Text =
            "Connected";

        ConnectionIndicator.Fill =
            Brushes.Green;


        ConnectButton.Content =
            "Disconnect";

        ConnectButton.IsEnabled =
            true;


        HostTextBox.IsEnabled =
            false;

        PortTextBox.IsEnabled =
            false;


        SetCommandButtons(
            true
        );
    }


    private void SetDisconnectedUi()
    {
        ConnectionStatusText.Text =
            "Disconnected";

        ConnectionIndicator.Fill =
            Brushes.Gray;


        ConnectButton.Content =
            "Connect";

        ConnectButton.IsEnabled =
            _protocolReady;


        HostTextBox.IsEnabled =
            true;

        PortTextBox.IsEnabled =
            true;


        SetCommandButtons(
            false
        );
    }


    private async Task DisconnectClientAsync(
        string logMessage
    )
    {
        KstpNetworkClient? client =
            _client;


        _client = null;


        if (
            client is not null
        )
        {
            await client.DisposeAsync();
        }


        SetDisconnectedUi();


        AppendLog(
            logMessage
        );
    }


    // ========================================================
    // ALLOCATE
    // ========================================================

    private async void AllocateButton_Click(
        object sender,
        RoutedEventArgs e
    )
    {
        if (
            !TryGetLockerId(
                out int lockerId
            )
        )
        {
            return;
        }


        string personId =
            PersonIdTextBox.Text.Trim();


        if (
            string.IsNullOrWhiteSpace(
                personId
            )
        )
        {
            AppendLog(
                "ERROR | Person ID is required."
            );

            return;
        }


        await SendCommandAsync(
            MessageType.AllocateLocker,
            new
            {
                locker_id = lockerId,
                person_id = personId,
            },
            $"ALLOCATE | locker={lockerId} | person={personId}"
        );
    }


    // ========================================================
    // OPEN
    // ========================================================

    private async void OpenButton_Click(
        object sender,
        RoutedEventArgs e
    )
    {
        if (
            !TryGetLockerId(
                out int lockerId
            )
        )
        {
            return;
        }


        await SendCommandAsync(
            MessageType.OpenLocker,
            new
            {
                locker_id = lockerId,
            },
            $"OPEN | locker={lockerId}"
        );
    }


    // ========================================================
    // RELEASE
    // ========================================================

    private async void ReleaseButton_Click(
        object sender,
        RoutedEventArgs e
    )
    {
        if (
            !TryGetLockerId(
                out int lockerId
            )
        )
        {
            return;
        }


        string personId =
            PersonIdTextBox.Text.Trim();


        if (
            string.IsNullOrWhiteSpace(
                personId
            )
        )
        {
            AppendLog(
                "ERROR | Person ID is required."
            );

            return;
        }


        await SendCommandAsync(
            MessageType.ReleaseLocker,
            new
            {
                locker_id = lockerId,
                person_id = personId,
            },
            $"RELEASE | locker={lockerId} | person={personId}"
        );
    }


    // ========================================================
    // SEND COMMAND
    // ========================================================

    private async Task SendCommandAsync(
        MessageType messageType,
        object payload,
        string description
    )
    {
        KstpNetworkClient? client =
            _client;


        if (
            client is null
            ||
            !client.IsConnected
        )
        {
            AppendLog(
                "ERROR | Not connected."
            );

            return;
        }


        uint requestId =
            checked(
                (uint)Interlocked.Increment(
                    ref _nextRequestId
                )
            );


        SetCommandButtons(
            false
        );


        AppendLog(
            $"TX | {description} | request={requestId}"
        );


        try
        {
            using CancellationTokenSource timeout =
                new(
                    TimeSpan.FromSeconds(
                        5
                    )
                );


            KstpFrame response =
                await client.SendRequestAsync(
                    messageType,
                    requestId,
                    payload,
                    timeout.Token
                );


            AppendLog(
                $"RX | {response.MessageType} "
                + $"| request={response.RequestId}"
            );


            AppendLog(
                "RX PAYLOAD | "
                + response.Payload.GetRawText()
            );
        }
        catch (Exception exc)
        {
            AppendLog(
                "COMMUNICATION ERROR | "
                + exc.GetType().Name
                + ": "
                + exc.Message
            );


            await DisconnectClientAsync(
                "Connection closed after communication error."
            );
        }
        finally
        {
            if (
                _client is not null
            )
            {
                SetCommandButtons(
                    true
                );
            }
        }
    }


    // ========================================================
    // VALIDATION
    // ========================================================

    private bool TryGetLockerId(
        out int lockerId
    )
    {
        if (
            !int.TryParse(
                LockerIdTextBox.Text.Trim(),
                out lockerId
            )
            ||
            lockerId <= 0
        )
        {
            AppendLog(
                "ERROR | Locker ID must be "
                + "a positive integer."
            );

            return false;
        }


        return true;
    }


    private void SetCommandButtons(
        bool enabled
    )
    {
        AllocateButton.IsEnabled =
            enabled;

        OpenButton.IsEnabled =
            enabled;

        ReleaseButton.IsEnabled =
            enabled;
    }


    // ========================================================
    // LOG
    // ========================================================

    private void AppendLog(
        string message
    )
    {
        string timestamp =
            DateTime.Now.ToString(
                "HH:mm:ss"
            );


        LogTextBox.AppendText(
            $"[{timestamp}] {message}"
            + Environment.NewLine
        );


        LogTextBox.ScrollToEnd();
    }


    private void ClearLogButton_Click(
        object sender,
        RoutedEventArgs e
    )
    {
        LogTextBox.Clear();
    }


    // ========================================================
    // APPLICATION SHUTDOWN
    // ========================================================

    private async void MainWindow_Closed(
        object? sender,
        EventArgs e
    )
    {
        KstpNetworkClient? client =
            _client;


        _client = null;


        if (
            client is not null
        )
        {
            await client.DisposeAsync();
        }
    }
}
