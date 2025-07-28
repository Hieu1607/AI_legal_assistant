# PowerShell script to run Newman API tests for AI Legal Assistant
# Usage: .\run_newman.ps1 [-Collection "file"] [-Environment "file"]

param(
    [string]$Collection = "postman\ai-legal-assistant.json",
    [string]$Environment = "postman\environment.json",
    [string]$OutputDir = "newman-results",
    [string]$ApiHost = "localhost",
    [int]$Port = 8000,
    [string]$AppModule = "app.main:app",
    [switch]$Help
)

# Colors for output
$Colors = @{
    Info = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
}

function Write-ColoredOutput {
    param([string]$Message, [string]$Type = "Info")
    Write-Host "[$Type] $Message" -ForegroundColor $Colors[$Type]
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Stop-BackgroundProcesses {
    Write-ColoredOutput "Cleaning up background processes..." "Info"
    Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" -or $_.CommandLine -like "*$AppModule*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
}

# Show help
if ($Help) {
    Write-Host @"
Usage: .\run_newman.ps1 [OPTIONS]

Options:
    -Collection FILE     Postman collection file (default: $Collection)
    -Environment FILE    Environment file (default: $Environment)
    -OutputDir DIR       Output directory (default: $OutputDir)
    -Host HOST           API host (default: $ApiHost)
    -Port PORT           API port (default: $Port)
    -Help                Show this help message

Examples:
    .\run_newman.ps1
    .\run_newman.ps1 -Collection "my-tests.json" -Port 8080
"@
    exit 0
}

Write-ColoredOutput "Starting Newman API tests for AI Legal Assistant" "Info"
Write-ColoredOutput "Collection: $Collection" "Info"
Write-ColoredOutput "Environment: $Environment" "Info"
Write-ColoredOutput "Output directory: $OutputDir" "Info"
Write-ColoredOutput "API URL: http://${ApiHost}:${Port}" "Info"

# Check dependencies
Write-ColoredOutput "Checking dependencies..." "Info"

$NewmanCmd = $null
if (Test-Command "newman") {
    $NewmanCmd = "newman"
}
elseif (Test-Command "npx") {
    Write-ColoredOutput "Newman not found globally, will use npx" "Warning"
    $NewmanCmd = "npx newman"
}
else {
    Write-ColoredOutput "Newman not found. Please install with: npm install -g newman" "Error"
    exit 1
}

if (-not (Test-Command "python")) {
    Write-ColoredOutput "Python not found. Please install Python" "Error"
    exit 1
}

if (-not (Test-Command "uvicorn")) {
    Write-ColoredOutput "Uvicorn not found. Please install with: pip install uvicorn" "Error"
    exit 1
}

# Check if collection file exists
if (-not (Test-Path $Collection)) {
    Write-ColoredOutput "Collection file not found: $Collection" "Warning"
    Write-ColoredOutput "Creating sample collection file..." "Info"

    $CollectionDir = Split-Path $Collection -Parent
    if ($CollectionDir -and -not (Test-Path $CollectionDir)) {
        New-Item -ItemType Directory -Path $CollectionDir -Force | Out-Null
    }

    $SampleCollection = @{
        info = @{
            name = "AI Legal Assistant API Tests"
            description = "Sample collection for AI Legal Assistant API"
            schema = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        }
        item = @(
            @{
                name = "Health Check"
                request = @{
                    method = "GET"
                    header = @()
                    url = @{
                        raw = "{{base_url}}/"
                        host = @("{{base_url}}")
                        path = @("")
                    }
                }
                event = @(
                    @{
                        listen = "test"
                        script = @{
                            exec = @(
                                "pm.test(`"Status code is 200`", function () {"
                                "    pm.response.to.have.status(200);"
                                "});"
                            )
                            type = "text/javascript"
                        }
                    }
                )
            }
            @{
                name = "Agent Query"
                request = @{
                    method = "POST"
                    header = @(
                        @{
                            key = "Content-Type"
                            value = "application/json"
                        }
                    )
                    body = @{
                        mode = "raw"
                        raw = "{`"question`": `"Chuong II dieu 29 bo luat hang hai noi gi?`", `"top_k`": 5, `"total_steps`": 1, `"timeout_sec`": 20}"
                    }
                    url = @{
                        raw = "{{base_url}}/agent"
                        host = @("{{base_url}}")
                        path = @("agent")
                    }
                }
                event = @(
                    @{
                        listen = "test"
                        script = @{
                            exec = @(
                                "pm.test(`"Status code is 200`", function () {"
                                "    pm.response.to.have.status(200);"
                                "});"
                                ""
                                "pm.test(`"Response has required fields`", function () {"
                                "    const responseJson = pm.response.json();"
                                "    pm.expect(responseJson).to.have.property(`"success`");"
                                "    pm.expect(responseJson).to.have.property(`"status_code`");"
                                "    pm.expect(responseJson).to.have.property(`"step_completed`");"
                                "    pm.expect(responseJson).to.have.property(`"data`");"
                                "    pm.expect(responseJson).to.have.property(`"message`");"
                                "    pm.expect(responseJson).to.have.property(`"execution_time`");"
                                "});"
                            )
                            type = "text/javascript"
                        }
                    }
                )
            }
        )
    }

    $SampleCollection | ConvertTo-Json -Depth 10 | Out-File -FilePath $Collection -Encoding UTF8
    Write-ColoredOutput "Sample collection created at: $Collection" "Success"
}

# Check if environment file exists, create if not
if (-not (Test-Path $Environment)) {
    Write-ColoredOutput "Creating environment file..." "Info"
    $EnvironmentDir = Split-Path $Environment -Parent
    if ($EnvironmentDir -and -not (Test-Path $EnvironmentDir)) {
        New-Item -ItemType Directory -Path $EnvironmentDir -Force | Out-Null
    }

    $EnvironmentData = @{
        id = [System.Guid]::NewGuid().ToString()
        name = "AI Legal Assistant Environment"
        values = @(
            @{
                key = "base_url"
                value = "http://${ApiHost}:${Port}"
                enabled = $true
            }
        )
    }

    $EnvironmentData | ConvertTo-Json -Depth 5 | Out-File -FilePath $Environment -Encoding UTF8
    Write-ColoredOutput "Environment file created at: $Environment" "Success"
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

try {
    # Start FastAPI server
    Write-ColoredOutput "Starting FastAPI server..." "Info"
    $ServerProcess = Start-Process -FilePath "uvicorn" -ArgumentList "$AppModule", "--host", $ApiHost, "--port", $Port, "--reload" -PassThru -WindowStyle Hidden

    # Wait for server to start
    Write-ColoredOutput "Waiting for server to start..." "Info"
    Start-Sleep 5

    # Check if server is running
    try {
        Invoke-WebRequest -Uri "http://${ApiHost}:${Port}/" -TimeoutSec 10 -ErrorAction Stop | Out-Null
        Write-ColoredOutput "Server is running at http://${ApiHost}:${Port}" "Success"
    }
    catch {
        Write-ColoredOutput "Server failed to start or is not responding" "Error"
        exit 1
    }

    # Run Newman tests
    Write-ColoredOutput "Running Newman tests..." "Info"

    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $HtmlReport = Join-Path $OutputDir "newman-report-$Timestamp.html"
    $JsonReport = Join-Path $OutputDir "newman-report-$Timestamp.json"

    $NewmanArgs = @(
        "run", $Collection,
        "--environment", $Environment,
        "--reporters", "html,json,cli",
        "--reporter-html-export", $HtmlReport,
        "--reporter-json-export", $JsonReport,
        "--timeout-request", "30000",
        "--bail",
        "--color", "on"
    )

    if ($NewmanCmd -eq "npx newman") {
        $Process = Start-Process -FilePath "npx" -ArgumentList (,@("newman") + $NewmanArgs) -Wait -PassThru -NoNewWindow
    }
    else {
        $Process = Start-Process -FilePath "newman" -ArgumentList $NewmanArgs -Wait -PassThru -NoNewWindow
    }

    $ExitCode = $Process.ExitCode

    if ($ExitCode -eq 0) {
        Write-ColoredOutput "All tests passed!" "Success"
        Write-ColoredOutput "HTML report: $HtmlReport" "Info"
        Write-ColoredOutput "JSON report: $JsonReport" "Info"
    }
    else {
        Write-ColoredOutput "Some tests failed (exit code: $ExitCode)" "Error"
        Write-ColoredOutput "Check reports for details:" "Info"
        Write-ColoredOutput "HTML report: $HtmlReport" "Info"
        Write-ColoredOutput "JSON report: $JsonReport" "Info"
    }

    Write-ColoredOutput "Newman tests completed" "Info"
    exit $ExitCode
}
finally {
    # Cleanup
    Stop-BackgroundProcesses
    if ($ServerProcess -and -not $ServerProcess.HasExited) {
        $ServerProcess.Kill()
    }
}
