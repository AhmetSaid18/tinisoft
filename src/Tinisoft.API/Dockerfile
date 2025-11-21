FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 5010

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Install dotnet ef tool globally
RUN dotnet tool install --global dotnet-ef --version 8.0.4

COPY ["src/Tinisoft.API/Tinisoft.API.csproj", "src/Tinisoft.API/"]
COPY ["src/Tinisoft.Application/Tinisoft.Application.csproj", "src/Tinisoft.Application/"]
COPY ["src/Tinisoft.Domain/Tinisoft.Domain.csproj", "src/Tinisoft.Domain/"]
COPY ["src/Tinisoft.Infrastructure/Tinisoft.Infrastructure.csproj", "src/Tinisoft.Infrastructure/"]
COPY ["src/Tinisoft.Shared/Tinisoft.Shared.csproj", "src/Tinisoft.Shared/"]

RUN dotnet restore "src/Tinisoft.API/Tinisoft.API.csproj"
COPY . .
WORKDIR "/src/src/Tinisoft.API"
RUN dotnet build "Tinisoft.API.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Tinisoft.API.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Use SDK image for final stage to have dotnet ef tool available
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS final
WORKDIR /app

# Install dotnet ef tool
RUN dotnet tool install --global dotnet-ef --version 8.0.4
ENV PATH="${PATH}:/root/.dotnet/tools"

# Copy published app
COPY --from=publish /app/publish .

# Copy source code for migrations (needed for dotnet ef)
COPY --from=build /src/src /src/src

WORKDIR /src/src/Tinisoft.API
ENTRYPOINT ["dotnet", "/app/Tinisoft.API.dll"]

