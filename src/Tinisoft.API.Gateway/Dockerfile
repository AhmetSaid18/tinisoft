FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 5000

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

COPY ["src/Tinisoft.API.Gateway/Tinisoft.API.Gateway.csproj", "src/Tinisoft.API.Gateway/"]
RUN dotnet restore "src/Tinisoft.API.Gateway/Tinisoft.API.Gateway.csproj"
COPY . .
WORKDIR "/src/src/Tinisoft.API.Gateway"
RUN dotnet build "Tinisoft.API.Gateway.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Tinisoft.API.Gateway.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Tinisoft.API.Gateway.dll"]

